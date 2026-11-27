import base64
from io import BytesIO
from PIL import Image
from django.test import TestCase, Client
from django.core.cache import cache
from .models import Company, User


class BrandingTests(TestCase):
    def setUp(self):
        cache.clear()
        self.addCleanup(cache.clear)
        self.owner = User.objects.create_user(username="brand-owner", role="COMPANY")
        self.company = Company.objects.create(owner=self.owner, name="Transport", city="Bamako", address="Gare", status="VERIFIED")
        self.other = User.objects.create_user(username="brand-other", role="TRAVELER")
        self.url = "/api/v1/auth/company/branding/"
        self.client.force_login(self.owner)

    def image(self):
        buf = BytesIO()
        Image.new("RGB", (300, 120), "#103b38").save(buf, format="PNG")
        return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()

    def test_normalizes_and_persists_only_own_branding(self):
        result = self.client.post(self.url, {"kind": "logo", "image": self.image()}, content_type="application/json")
        self.assertEqual(result.status_code, 200, result.content)
        self.company.refresh_from_db()
        self.assertTrue(self.company.logo.startswith("data:image/jpeg;base64,"))
        self.assertEqual(result.json()["company"]["logo"], self.company.logo)
        self.assertEqual(self.client.get("/api/v1/auth/company/").json()["logo"], self.company.logo)
        self.assertEqual(self.client.post(self.url, {"kind": "logo", "image": ""}, content_type="application/json").status_code, 200)
        self.company.refresh_from_db()
        self.assertEqual(self.company.logo, "")

    def test_rejects_svg_invalid_and_unauthorized(self):
        for value in ("data:image/svg+xml;base64,AAAA", "data:image/png;base64,AAAA", "https://example.org/a.png"):
            self.assertEqual(self.client.post(self.url, {"kind":"banner","image":value}, content_type="application/json").status_code, 400)
        self.client.force_login(self.other)
        self.assertEqual(self.client.post(self.url, {"kind":"banner","image":self.image()}, content_type="application/json").status_code, 403)
        self.client.logout()
        self.assertEqual(self.client.post(self.url, {"kind":"banner","image":self.image()}, content_type="application/json").status_code, 401)
        self.company.refresh_from_db()
        self.assertEqual(self.company.banner, "")

    def test_suspended_and_csrf_protected(self):
        self.company.status = "SUSPENDED"
        self.company.save(update_fields=["status"])
        self.assertEqual(self.client.post(self.url, {"kind":"banner","image":self.image()}, content_type="application/json").status_code, 403)
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.owner)
        self.assertEqual(client.post(self.url, {"kind":"banner","image":self.image()}, content_type="application/json").status_code, 403)
