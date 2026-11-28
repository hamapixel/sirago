from django.contrib import admin
from django.core.cache import cache
from django.test import Client, TestCase, override_settings
from accounts.models import User


# Legacy password-only admin mode; mandatory MFA denial is covered in accounts.test_mfa.
@override_settings(SIRAGO_ADMIN_MFA_REQUIRED=False)
class AdminSecurityTests(TestCase):
    def setUp(self):
        cache.clear()
        self.addCleanup(cache.clear)
        self.password = "Admin!Secure2026"
        self.admin = User.objects.create_superuser(username="admin-security", password=self.password)
        self.staff = User.objects.create_user(username="staff-security", password=self.password, is_staff=True)
        self.traveler = User.objects.create_user(username="traveler-security", password=self.password)

    def submit_login(self, user, password=None, client=None, **headers):
        return (client or self.client).post(
            "/admin/login/",
            {"username": user.username, "password": password if password is not None else self.password, "next": "/admin/"},
            **headers,
        )

    def test_superuser_can_login_and_reach_existing_admin_models(self):
        result = self.submit_login(self.admin)
        self.assertRedirects(result, "/admin/")
        self.assertEqual(self.client.get("/admin/accounts/company/").status_code, 200)
        self.assertEqual(self.client.get("/api/v1/auth/me/").json()["role"], "ADMIN")

    def test_non_superusers_cannot_login_to_admin(self):
        for user in (self.staff, self.traveler):
            with self.subTest(user=user.username):
                self.assertEqual(self.submit_login(user).status_code, 200)
                self.assertNotIn("_auth_user_id", self.client.session)

    def test_existing_non_superuser_session_cannot_access_admin(self):
        for user in (self.staff, self.traveler):
            self.client.force_login(user)
            self.assertEqual(self.client.get("/admin/").status_code, 302)
            self.assertEqual(self.client.get("/admin/accounts/user/").status_code, 302)
            self.assertEqual(self.client.get("/admin/accounts/company/").status_code, 302)
        self.assertTrue(admin.site.is_registered(User))

    def test_admin_login_is_rate_limited_without_trusting_forwarded_ip(self):
        for n in range(10):
            self.submit_login(self.admin, "wrong", HTTP_X_FORWARDED_FOR=f"192.0.2.{n + 1}")
        result = self.submit_login(self.admin, HTTP_X_FORWARDED_FOR="192.0.2.99")
        self.assertEqual(result.status_code, 200)
        self.assertContains(result, "Trop de tentatives")
        self.assertNotIn("_auth_user_id", self.client.session)
        cache.clear()
        self.assertRedirects(self.submit_login(self.admin), "/admin/")

    def test_admin_login_keeps_csrf_protection(self):
        client = Client(enforce_csrf_checks=True)
        self.assertEqual(self.submit_login(self.admin, client=client).status_code, 403)
        client.get("/admin/login/")
        token = client.cookies["csrftoken"].value
        result = client.post("/admin/login/", {
            "username": self.admin.username,
            "password": self.password,
            "next": "/admin/",
            "csrfmiddlewaretoken": token,
        })
        self.assertRedirects(result, "/admin/")
