from uuid import uuid4
from unittest.mock import patch
from django.test import TestCase, Client, override_settings
from django.utils import timezone
from accounts.models import Company, CompanyCommission, User
from .models import Booking, SandboxCheckout, SandboxSettlement
from .test_booking import BookingFixture
from .commissions import freeze_commissions

@override_settings(DEBUG=True,SIRAGO_ENABLE_SIMULATED_PAYMENTS=True)
class SettlementTests(BookingFixture,TestCase):
    def setUp(self):
        super().setUp()
        env=patch.dict("os.environ",{"SIRAGO_ENABLE_SASPAY_SANDBOX":"1","SIRAGO_ENABLE_SASPAY_TICKETS":"1","SASPAY_API_KEY":"sk_test_example","SIRAGO_ENV":"development"})
        env.start();self.addCleanup(env.stop)
        self.admin=User.objects.create_superuser(username="settlement-admin",password="test-password")
        self.client.force_login(self.user)
        r=self.reserve()
        self.assertEqual(r.status_code,201,r.content)
        b=Booking.objects.get(pk=r.json()["id"])
        CompanyCommission.objects.create(company=self.company,rate_bps=500)
        self.checkout=SandboxCheckout.objects.create(booking=b,amount=16000,status="PAID",provider_id=uuid4(),transaction_id=uuid4(),issued_at=timezone.now())
        freeze_commissions(self.checkout,list(b.legs.all()))
        b.status=Booking.Status.TEST_PAID;b.save(update_fields=["status"])
        self.client.force_login(self.admin)
        self.base="/api/v1/auth/supervision/settlements/"
        self.owner_url="/api/v1/auth/company/settlements/"
        self.url=self.base+str(self.company.pk)+"/"
    def post(self,amount,expected,ref=None,client=None):
        return (client or self.client).post(self.url,{"amount":amount,"expected_remaining":expected,"reference":str(ref or uuid4())},content_type="application/json")
    def balances(self):
        r=self.client.get(self.base)
        self.assertEqual(r.status_code,200,r.content)
        return r.json()
    def pdf(self,pk):
        return "/api/v1/auth/settlements/"+str(pk)+"/pdf/"
    def test_partial_and_full_with_idempotency(self):
        before=self.balances()["summary"]
        self.assertEqual((before["gross"],before["commission"],before["remaining"]),(16000,800,15200))
        ref=uuid4()
        r=self.post(5000,15200,ref)
        self.assertEqual(r.status_code,201,r.content)
        self.assertEqual(self.post(5000,15200,ref).status_code,200)
        self.assertEqual(self.post(6000,15200,ref).status_code,409)
        self.assertEqual(self.post(10200,10200).status_code,201)
        self.assertEqual(self.post(1,1).status_code,409)
        self.assertEqual(SandboxSettlement.objects.count(),2)
        after=self.balances()["summary"]
        self.assertEqual((after["remaining"],after["settled"]),(0,15200))
        self.assertEqual(self.client.get(self.base+"history/",{"q":str(ref)}).json()["total"],1)
    def test_invalid_stale_and_pending(self):
        for amount in (True,0,-1,2.5,"100",15201):
            self.assertEqual(self.post(amount,15200).status_code,400)
        self.assertEqual(self.post(100,15000).status_code,409)
        self.checkout.status="PENDING";self.checkout.save(update_fields=["status"])
        self.assertEqual(self.balances()["summary"]["remaining"],0)
        self.assertEqual(self.post(100,15200).status_code,409)
        self.assertFalse(SandboxSettlement.objects.exists())
    def test_owner_privacy_and_receipt(self):
        r=self.post(5000,15200);self.assertEqual(r.status_code,201,r.content);pk=r.json()["id"]
        self.assertTrue(self.client.get(self.pdf(pk)).content.startswith(b"%PDF"))
        self.client.force_login(self.owner)
        d=self.client.get(self.owner_url).json()
        self.assertEqual(d["balance"]["remaining"],10200)
        self.assertEqual(d["total"],1)
        self.assertEqual(self.client.get(self.pdf(pk)).status_code,200)
        self.assertEqual(self.client.get(self.base).status_code,403)
        self.assertEqual(self.post(100,10200).status_code,403)
        owner=User.objects.create_user(username="other-settlement-owner",role=User.Role.COMPANY)
        Company.objects.create(owner=owner,name="Other",city="Mopti",address="Gare",status="VERIFIED")
        self.client.force_login(owner)
        self.assertEqual(self.client.get(self.owner_url).json()["total"],0)
        self.assertEqual(self.client.get(self.pdf(pk)).status_code,404)
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(self.owner_url).status_code,403)
        self.client.logout()
        self.assertEqual(self.client.get(self.pdf(pk)).status_code,401)
    def test_disabled_and_csrf(self):
        with patch.dict("os.environ",{"SIRAGO_ENABLE_SASPAY_TICKETS":"0"}):
            self.assertEqual(self.post(100,15200).status_code,403)
        c=Client(enforce_csrf_checks=True);c.force_login(self.admin)
        self.assertEqual(self.post(100,15200,client=c).status_code,403)
        token=c.get("/api/v1/auth/csrf/").json()["csrfToken"]
        r=c.post(self.url,{"amount":100,"expected_remaining":15200,"reference":str(uuid4())},content_type="application/json",HTTP_X_CSRFTOKEN=token)
        self.assertEqual(r.status_code,201,r.content)
    def test_search_and_unconfigured(self):
        self.assertEqual(self.client.get(self.base,{"q":"Transport Bamako"}).json()["total"],1)
        self.assertEqual(self.client.get(self.base,{"q":"absent"}).json()["summary"]["remaining"],0)
        self.checkout.commission_lines.update(rate_bps=None,commission=None,company_share=None)
        self.assertEqual(self.balances()["summary"]["remaining"],0)
        self.assertEqual(self.post(100,15200).status_code,409)
