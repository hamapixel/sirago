from datetime import timedelta
from unittest.mock import patch
from uuid import uuid4
from django.test import TestCase,override_settings
from accounts.test_helpers import force_mfa_login
from django.utils import timezone
from accounts.models import CompanyCommission,User
from .models import Booking,BookingLeg,SandboxCheckout,SandboxCommission,Route,Departure
from .test_booking import BookingFixture
from .commissions import fee_per_ticket,freeze_commissions
from .sandbox_reconcile import reconcile

@override_settings(DEBUG=True,SIRAGO_ENABLE_SIMULATED_PAYMENTS=True,SIRAGO_ADMIN_MFA_REQUIRED=True)
class CommissionLedgerTests(BookingFixture,TestCase):
    def setUp(self):
        super().setUp()
        env=patch.dict("os.environ",{"SIRAGO_ENABLE_SASPAY_SANDBOX":"1","SIRAGO_ENABLE_SASPAY_TICKETS":"1","SASPAY_API_KEY":"sk_test_example","SIRAGO_ENV":"development"})
        env.start();self.addCleanup(env.stop)
        self.admin=User.objects.create_superuser(username="ledger-admin",password="test-password")
        self.client.force_login(self.user)
        self.ledger="/api/v1/auth/supervision/commissions/ledger/"
    def checkout(self,**kwargs):
        r=self.reserve(**kwargs)
        self.assertEqual(r.status_code,201,r.content)
        b=Booking.objects.get(pk=r.json()["id"])
        with patch("fleet.sandbox_views.create_booking_checkout",return_value=(str(uuid4()),"https://sandbox-checkout.saspay.me/test")) as create:
            url=f"/api/v1/travel/bookings/{b.pk}/sandbox-checkout/"
            r=self.client.post(url,{},content_type="application/json")
            self.assertEqual(r.status_code,201,r.content)
            self.assertEqual(self.client.post(url,{},content_type="application/json").status_code,200)
            self.assertEqual(create.call_count,1)
        return SandboxCheckout.objects.get(booking=b)
    def paid(self,a,status="PAID"):
        with patch("fleet.sandbox_reconcile.inspect_booking_checkout",return_value=(status,str(uuid4()))):
            reconcile(a.pk)
        a.refresh_from_db()
    def report(self,**params):
        force_mfa_login(self.client, self.admin)
        r=self.client.get(self.ledger,params)
        self.assertEqual(r.status_code,200,r.content)
        return r.json()
    def test_frozen_rate_and_recognition(self):
        policy=CompanyCommission.objects.create(company=self.company,rate_bps=500)
        a=self.checkout()
        row=a.commission_lines.get()
        self.assertEqual((row.gross,row.commission,row.company_share),(16000,800,15200))
        self.assertEqual(self.report()["summary"]["gross"],0)
        policy.rate_bps=300;policy.save()
        self.paid(a)
        reconcile(a.pk)
        self.assertEqual(a.commission_lines.count(),1)
        r=self.report(q="Transport Sikasso")
        self.assertEqual(r["total"],1)
        self.assertEqual(r["items"][0]["rate_bps"],500)
        self.assertEqual(r["summary"]["commission"],800)
        self.assertEqual(r["summary"]["company_share"],15200)
        self.assertEqual(self.report(date_from="2000-01-01",date_to="2000-01-02")["total"],0)
    def test_missing_rate_not_backfilled(self):
        a=self.checkout()
        CompanyCommission.objects.create(company=self.company,rate_bps=500)
        self.paid(a)
        r=self.report()
        self.assertIsNone(r["items"][0]["rate_bps"])
        self.assertEqual(r["summary"]["unconfigured"],16000)
        self.assertEqual(r["summary"]["commission"],0)
        self.assertIsNone(r["items"][0]["company_share"])
    def test_explicit_zero(self):
        CompanyCommission.objects.create(company=self.company,rate_bps=0)
        a=self.checkout();self.paid(a)
        r=self.report()
        self.assertEqual(r["summary"]["company_share"],16000)
        self.assertEqual(r["summary"]["unconfigured"],0)
    def test_rounding_mixed_categories(self):
        self.assertEqual(fee_per_ticket(110,500),6)
        self.client.force_login(self.user)
        b=Booking.objects.get(pk=self.reserve().json()["id"])
        l=b.legs.get();l.unit_price=110;l.premium_count=1;l.premium_unit_price=130;l.save()
        CompanyCommission.objects.create(company=self.company,rate_bps=500)
        a=SandboxCheckout.objects.create(booking=b,amount=240)
        freeze_commissions(a,[l])
        r=a.commission_lines.get()
        self.assertEqual((r.gross,r.commission,r.company_share),(240,13,227))
    def test_late_payment_not_recognized(self):
        CompanyCommission.objects.create(company=self.company,rate_bps=500)
        a=self.checkout();self.paid(a,"LATE_PAID")
        self.assertEqual(self.report()["total"],0)
        self.assertEqual(a.commission_lines.count(),1)
    def test_return_and_permissions(self):
        CompanyCommission.objects.create(company=self.company,rate_bps=500)
        route=Route.objects.create(company=self.company,origin="Sikasso",destination="Bamako",boarding_point="B",arrival_point="A",duration_minutes=420,price=7000)
        ret=Departure.objects.create(company=self.company,bus=self.departure.bus,route=route,starts_at=self.start+timedelta(hours=8),ends_at=self.start+timedelta(hours=15),price=7000,capacity=2,status="PUBLISHED")
        a=self.checkout(ret=ret.pk,total=30000);self.paid(a)
        self.assertEqual(self.report()["summary"]["commission"],1500)
        self.assertEqual(self.report()["total"],2)
        self.client.force_login(self.owner)
        self.assertEqual(self.client.get(self.ledger).status_code,403)
        self.client.logout()
        self.assertEqual(self.client.get(self.ledger).status_code,401)
