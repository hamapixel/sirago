from django.test import TestCase,override_settings
from accounts.models import CompanyAgent,User,Company
from .test_booking import BookingFixture
from .models import TestBoarding

@override_settings(DEBUG=True,SIRAGO_ENABLE_SIMULATED_PAYMENTS=True)
class AgentPermissionTests(BookingFixture,TestCase):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.user)
        r=self.reserve()
        self.assertEqual(r.status_code,201)
        base=f'/api/v1/travel/bookings/{r.json()["id"]}/'
        self.assertEqual(self.client.post(base+"simulate-payment/",{"network":"orange_ml"},content_type="application/json").status_code,200)
        self.code=self.client.get(base+"tickets/").json()["items"][0]["code"]
        self.agent=User.objects.create_user(username="controller",role=User.Role.COMPANY)
        self.membership=CompanyAgent.objects.create(user=self.agent,company=self.departure.company,role="CONTROLLER")
        self.client.force_login(self.agent)
        self.base="/api/v1/company/"
        self.manifest=self.base+f"departures/{self.departure.pk}/manifest/"
    def post(self,path,values):
        return self.client.post(self.base+path,values,content_type="application/json")
    def test_controller_allowlist_and_manifest_redaction(self):
        for path in ("dashboard/","buses/","routes/","reservations/"):
            self.assertEqual(self.client.get(self.base+path).status_code,403)
        self.assertEqual(self.client.get(self.base+"departures/").status_code,200)
        self.assertEqual(self.post("departures/",{}).status_code,403)
        self.assertEqual(self.post(f"departures/{self.departure.pk}/status/",{"status":"CANCELLED"}).status_code,403)
        r=self.client.get(self.manifest)
        self.assertEqual(r.status_code,200)
        self.assertNotIn("real_amount",r.json())
        self.assertNotIn("simulated_amount",r.json())
        self.assertNotIn("amount",r.json()["items"][0])
        self.assertTrue(self.client.get(self.manifest+"pdf/").content.startswith(b"%PDF"))
        self.assertEqual(self.post("boarding/lookup/",{"code":self.code}).status_code,200)
        self.assertEqual(self.post("boarding/validate/",{"code":self.code,"passengers":[0]}).status_code,200)
        self.assertEqual(TestBoarding.objects.get().actor,self.agent)
    def test_clerk_and_cross_company(self):
        self.membership.role="CLERK";self.membership.save(update_fields=["role"])
        r=self.client.get(self.base+"reservations/")
        self.assertEqual(r.status_code,200)
        self.assertNotIn("total",r.json()["items"][0])
        other=User.objects.create_user(username="other-owner",role=User.Role.COMPANY)
        c=Company.objects.create(owner=other,name="Autre",city="Bamako",address="Gare",status="VERIFIED")
        self.membership.company=c;self.membership.save(update_fields=["company"])
        self.assertEqual(self.client.get(self.manifest).status_code,404)
        self.assertEqual(self.post("boarding/lookup/",{"code":self.code}).status_code,404)
    def test_suspended_company(self):
        Company.objects.filter(pk=self.membership.company_id).update(status="SUSPENDED")
        self.assertEqual(self.client.get(self.manifest).status_code,403)
        self.assertEqual(self.post("boarding/lookup/",{"code":self.code}).status_code,403)
