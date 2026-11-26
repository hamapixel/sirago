from django.test import TestCase,override_settings
from django.utils import timezone
from datetime import timedelta
from accounts.models import Company,User
from .test_booking import BookingFixture
from .models import Booking

@override_settings(DEBUG=True,SIRAGO_ENABLE_SIMULATED_PAYMENTS=True)
class ManifestTests(BookingFixture,TestCase):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.user)
        r=self.reserve()
        self.assertEqual(r.status_code,201)
        self.base=f'/api/v1/travel/bookings/{r.json()["id"]}/'
        self.manifest_url=f"/api/v1/company/departures/{self.departure.pk}/manifest/"
    def test_pending_and_expiration(self):
        self.client.force_login(self.owner)
        r=self.client.get(self.manifest_url).json()
        self.assertEqual((r["reserved"],r["pending"],r["remaining"],r["pending_amount"],r["real_amount"]),(2,2,0,16000,0))
        Booking.objects.all().update(expires_at=timezone.now()-timedelta(seconds=1))
        self.assertEqual(self.client.get(self.manifest_url).json()["reserved"],0)
    def test_simulated_and_boarding_and_pdf(self):
        self.assertEqual(self.client.post(self.base+"simulate-payment/",{"network":"orange_ml"},content_type="application/json").status_code,200)
        code=self.client.get(self.base+"tickets/").json()["items"][0]["code"]
        self.client.force_login(self.owner)
        self.assertEqual(self.client.post("/api/v1/company/boarding/validate/",{"code":code,"passengers":[0]},content_type="application/json").status_code,200)
        r=self.client.get(self.manifest_url).json()
        self.assertEqual((r["simulated_amount"],r["real_amount"],r["boarded"],r["waiting"],r["absent"]),(16000,0,1,1,0))
        self.assertEqual([x["state"] for x in r["items"]],["BOARDED","WAITING"])
        pdf=self.client.get(self.manifest_url+"pdf/")
        self.assertEqual(pdf.status_code,200)
        self.assertTrue(pdf.content.startswith(b"%PDF"))
        self.assertIn("no-store",pdf["Cache-Control"])
    def test_isolation(self):
        self.assertEqual(self.client.get(self.manifest_url).status_code,403)
        other=User.objects.create_user(username="manifest-other",role=User.Role.COMPANY)
        Company.objects.create(owner=other,name="Autre",city="Bamako",address="Gare",status="VERIFIED")
        self.client.force_login(other)
        self.assertEqual(self.client.get(self.manifest_url).status_code,404)
        self.assertEqual(self.client.get(self.manifest_url+"pdf/").status_code,404)
