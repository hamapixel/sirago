from django.test import TestCase, override_settings
from accounts.models import Company,User
from .test_booking import BookingFixture
from .models import TestBoarding

@override_settings(DEBUG=True,SIRAGO_ENABLE_SIMULATED_PAYMENTS=True)
class BoardingTests(BookingFixture,TestCase):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.user)
        r=self.reserve()
        self.assertEqual(r.status_code,201)
        base=f'/api/v1/travel/bookings/{r.json()["id"]}/'
        self.assertEqual(self.client.post(base+"simulate-payment/",{"network":"orange_ml"},content_type="application/json").status_code,200)
        self.code=self.client.get(base+"tickets/").json()["items"][0]["code"]
        self.client.force_login(self.owner)
    def post(self,action,**kwargs):
        return self.client.post("/api/v1/company/boarding/"+action+"/",{"code":self.code,**kwargs},content_type="application/json")
    def test_partial_then_complete_and_retry(self):
        r=self.post("lookup")
        self.assertEqual(r.status_code,200,r.content)
        self.assertEqual(r.json()["remaining"],2)
        self.assertEqual(self.post("validate",passengers=[0]).json()["boarded"],1)
        self.assertEqual(self.post("validate",passengers=[0,1]).json()["remaining"],0)
        self.assertEqual(self.post("validate",passengers=[1]).json()["boarded"],2)
        self.assertEqual(TestBoarding.objects.count(),2)
        self.assertEqual(len(self.client.get("/api/v1/company/boarding/history/").json()["items"]),2)
    def test_invalid_selection(self):
        for value in ([2],[True],[0,0],[]):
            self.assertEqual(self.post("validate",passengers=value).status_code,400)
        self.assertFalse(TestBoarding.objects.exists())
    def test_other_company_and_traveler(self):
        owner=User.objects.create_user(username="other-company",role=User.Role.COMPANY)
        Company.objects.create(owner=owner,name="Autre",city="Bamako",address="Gare",status="VERIFIED")
        self.client.force_login(owner)
        self.assertEqual(self.post("lookup").status_code,404)
        self.assertEqual(self.post("validate",passengers=[0]).status_code,404)
        self.client.force_login(self.user)
        self.assertEqual(self.post("lookup").status_code,403)
    def test_disabled_and_suspended(self):
        with override_settings(DEBUG=False):
            self.assertEqual(self.post("lookup").status_code,404)
        self.departure.status="SUSPENDED"
        self.departure.save(update_fields=["status"])
        self.assertEqual(self.post("validate",passengers=[0]).status_code,409)

    def test_history_search_and_filters(self):
        self.owner.first_name="Agent"
        self.owner.last_name="Test"
        self.owner.save(update_fields=["first_name","last_name"])
        self.assertEqual(self.post("validate",passengers=[0,1]).status_code,200)
        url="/api/v1/company/boarding/history/"
        r=self.client.get(url,{"q":"Moussa","page_size":10})
        self.assertEqual(r.status_code,200,r.content)
        self.assertEqual(r.json()["total"],1)
        self.assertEqual(r.json()["items"][0]["name"],"Moussa Test")
        self.assertEqual(r.json()["items"][0]["agent"],"Agent Test")
        self.assertEqual(self.client.get(url,{"q":"Agent Test"}).json()["total"],2)
        self.assertEqual(self.client.get(url,{"q":"introuvable"}).json()["total"],0)
        self.assertEqual(self.client.get(url,{"date":"2000-01-01"}).json()["total"],0)
        self.assertEqual(self.client.get(url,{"page_size":0}).status_code,400)

    def test_company_search_across_pages(self):
        from datetime import timedelta
        from .models import Departure
        for i in range(11):
            starts=self.start+timedelta(days=i+1)
            Departure.objects.create(company=self.company,bus=self.departure.bus,route=self.departure.route,starts_at=starts,ends_at=starts+timedelta(hours=7),price=8000,capacity=2,status="PUBLISHED")
        url="/api/v1/company/departures/"
        first=self.client.get(url,{"q":"Bamako Sikasso","page_size":10}).json()
        second=self.client.get(url,{"q":"Bamako Sikasso","page_size":10,"page":2}).json()
        self.assertEqual(first["total"],12)
        self.assertEqual(len(first["items"]),10)
        self.assertEqual(len(second["items"]),2)
        self.assertFalse(set(x["id"] for x in first["items"]) & set(x["id"] for x in second["items"]))
        self.assertEqual(self.client.get("/api/v1/company/reservations/",{"q":"Moussa"}).json()["total"],1)
        self.assertEqual(self.client.get("/api/v1/company/reservations/",{"q":"introuvable"}).json()["total"],0)
