from django.test import TestCase, override_settings
from .test_booking import BookingFixture

@override_settings(DEBUG=True,SIRAGO_ENABLE_SIMULATED_PAYMENTS=True)
class TicketTests(BookingFixture,TestCase):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.user)
        r=self.reserve(ticket_mode="individual")
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

    def test_collective_default_and_capacity_100(self):
        from uuid import uuid4
        self.client.post(self.base+"cancel/")
        self.departure.bus.capacity=100
        self.departure.bus.save(update_fields=["capacity"])
        self.departure.capacity=100
        self.departure.save(update_fields=["capacity"])
        r=self.reserve(count=100,passenger_names=[f"Passager {i}" for i in range(100)],total=800000,request_id=str(uuid4()))
        self.assertEqual(r.status_code,201,r.content)
        self.assertEqual(r.json()["ticket_mode"],"group")
        self.base=f'/api/v1/travel/bookings/{r.json()["id"]}/'
        self.url=self.base+"tickets/"
        self.pay()
        items=self.client.get(self.url).json()["items"]
        self.assertEqual(len(items),1)
        self.assertEqual(items[0]["count"],100)
        self.assertEqual(items[0]["amount"],800000)
        self.assertEqual(len(items[0]["names"]),100)
        self.assertEqual(self.client.get(self.url+"0/1/pdf/").status_code,404)
        self.assertTrue(self.client.get(self.url+"0/0/pdf/").content.startswith(b"%PDF"))
        self.assertEqual(self.search()["total"],0)

    def test_mixed_collective_and_choice_immutable(self):
        from uuid import uuid4
        self.client.post(self.base+"cancel/")
        self.departure.bus.capacity=5
        self.departure.bus.premium_capacity=2
        self.departure.bus.save(update_fields=["capacity","premium_capacity"])
        self.departure.capacity=5
        self.departure.premium_capacity=2
        self.departure.premium_price=12000
        self.departure.save(update_fields=["capacity","premium_capacity","premium_price"])
        payload=dict(count=5,passenger_names=["Awa Test","Moussa Test","Awa Test","Baba Test","Ami Test"],premium_positions=[[3,4]],total=48000,request_id=str(uuid4()))
        r=self.reserve(**payload)
        self.assertEqual(r.status_code,201,r.content)
        self.assertEqual(self.reserve(**payload,ticket_mode="individual").status_code,409)
        self.base=f'/api/v1/travel/bookings/{r.json()["id"]}/'
        self.url=self.base+"tickets/"
        self.pay()
        items=self.client.get(self.url).json()["items"]
        self.assertEqual([(t["category"],t["count"],t["amount"]) for t in items],[("Standard",3,24000),("Premium",2,24000)])
        self.assertNotEqual(items[0]["code"],items[1]["code"])
        self.assertEqual(items[0]["names"].count("Awa Test"),2)
