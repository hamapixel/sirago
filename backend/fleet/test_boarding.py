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
