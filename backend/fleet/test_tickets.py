from django.test import TestCase, override_settings
from .test_booking import BookingFixture

@override_settings(DEBUG=True,SIRAGO_ENABLE_SIMULATED_PAYMENTS=True)
class TicketTests(BookingFixture,TestCase):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.user)
        r=self.reserve()
        self.assertEqual(r.status_code,201)
        self.base=f'/api/v1/travel/bookings/{r.json()["id"]}/'
        self.url=self.base+"tickets/"
    def pay(self):
        self.assertEqual(self.client.post(self.base+"simulate-payment/",{"network":"orange_ml"},content_type="application/json").status_code,200)
    def test_unpaid_and_private(self):
        self.assertEqual(self.client.get(self.url).status_code,409)
        self.pay()
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(self.url).status_code,404)
        self.assertEqual(self.client.get(self.url+"0/0/pdf/").status_code,404)
        self.client.logout()
        self.assertEqual(self.client.get(self.url).status_code,401)
    def test_individual_stable_qr_and_price(self):
        self.pay()
        r=self.client.get(self.url)
        self.assertEqual(r.status_code,200)
        a,b=r.json()["items"]
        self.assertNotEqual(a["code"],b["code"])
        self.assertNotEqual(a["qr"],b["qr"])
        self.assertTrue(a["code"].startswith("SRG-TEST-"))
        self.assertEqual(a["name"],"Awa Test")
        self.assertEqual(a["amount"],8000)
        self.assertEqual(r.json(),self.client.get(self.url).json())
        self.assertIn("no-store",r["Cache-Control"])
    def test_pdf_and_bounds(self):
        self.pay()
        r=self.client.get(self.url+"0/1/pdf/")
        self.assertEqual(r.status_code,200)
        self.assertTrue(r.content.startswith(b"%PDF"))
        self.assertIn("SRG-TEST-",r["Content-Disposition"])
        self.assertIn("no-store",r["Cache-Control"])
        self.assertEqual(self.client.get(self.url+"0/2/pdf/").status_code,404)
        self.assertEqual(self.client.get(self.url+"2/0/pdf/").status_code,404)
    def test_disabled_in_production(self):
        self.pay()
        with override_settings(DEBUG=False):
            self.assertEqual(self.client.get(self.url).status_code,404)
            self.assertEqual(self.client.get(self.url+"0/0/pdf/").status_code,404)
