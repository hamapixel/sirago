from datetime import timedelta
from uuid import uuid4
from django.test import TestCase,override_settings
from accounts.models import Company,CompanyAgent,User
from .models import Booking,Departure
from .test_booking import BookingFixture

@override_settings(DEBUG=True,SIRAGO_ENABLE_SIMULATED_PAYMENTS=True)
class FinanceTests(BookingFixture,TestCase):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.user)
        r=self.reserve()
        self.assertEqual(r.status_code,201,r.content)
        self.base=f'/api/v1/travel/bookings/{r.json()["id"]}/'
        self.id=r.json()["id"]
        self.url="/api/v1/company/finance/"
        self.day=self.start.date().isoformat()
    def finance(self,**kw):
        self.client.force_login(self.owner)
        return self.client.get(self.url,{"date_from":self.day,"date_to":self.day,**kw})
    def pay(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.post(self.base+"simulate-payment/",{"network":"orange_ml"},content_type="application/json").status_code,200)
    def test_pending_then_simulated(self):
        s=self.finance().json()["summary"]
        self.assertEqual((s["pending_amount"],s["simulated_amount"],s["real_amount"]),(16000,0,0))
        self.pay()
        r=self.finance().json()
        self.assertEqual((r["summary"]["pending_amount"],r["summary"]["simulated_amount"],r["summary"]["orange_amount"],r["summary"]["real_amount"]),(0,16000,16000,0))
        self.assertEqual(r["items"][0]["simulated_passengers"],2)
        self.assertEqual(self.finance(q="introuvable").json()["summary"]["simulated_amount"],0)
    def test_report_excludes_original_and_counts_replacement(self):
        self.pay()
        target=Departure.objects.create(company=self.company,bus=self.departure.bus,route=self.departure.route,starts_at=self.start+timedelta(days=1),ends_at=self.start+timedelta(days=1,hours=7),price=9000,capacity=2,status="PUBLISHED")
        r=self.client.post(self.base+"report/",{"departure_id":target.pk,"total":9000,"passengers":[1]},content_type="application/json")
        self.assertEqual(r.status_code,201,r.content)
        self.assertEqual(self.finance().json()["summary"]["simulated_amount"],8000)
        data=self.finance(date_to=target.starts_at.date().isoformat()).json()
        self.assertEqual(data["summary"]["simulated_amount"],17000)
        self.assertEqual(data["summary"]["simulated_passengers"],2)
        self.assertEqual(data["total"],2)
    def test_expired_and_invalid_filters(self):
        from django.utils import timezone
        Booking.objects.filter(pk=self.id).update(expires_at=timezone.now()-timedelta(seconds=1))
        self.assertEqual(self.finance().json()["summary"]["pending_amount"],0)
        self.assertEqual(self.finance(date_from="bad").status_code,400)
        self.assertEqual(self.finance(date_from="2000-01-01").status_code,400)
        self.assertEqual(self.finance(page=0).status_code,400)
    def test_owner_only_and_company_isolation(self):
        self.assertEqual(self.client.get(self.url).status_code,403)
        other=User.objects.create_user(username="other-finance",role="COMPANY")
        Company.objects.create(owner=other,name="Other",city="Bamako",address="Gare",status="VERIFIED")
        self.client.force_login(other)
        self.assertEqual(self.client.get(self.url,{"date_from":self.day,"date_to":self.day}).json()["summary"]["pending_amount"],0)
        for role in ("CLERK","CONTROLLER"):
            agent=User.objects.create_user(username=role,role="COMPANY")
            CompanyAgent.objects.create(user=agent,company=self.company,role=role)
            self.client.force_login(agent)
            self.assertEqual(self.client.get(self.url).status_code,403)
        self.client.logout()
        self.assertEqual(self.client.get(self.url).status_code,401)
