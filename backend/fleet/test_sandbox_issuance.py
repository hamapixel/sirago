import hashlib,hmac,json,time
from datetime import timedelta
from unittest.mock import patch
from uuid import uuid4
from django.test import TestCase, Client, override_settings
from django.utils import timezone
from accounts.models import Notification
from .models import Booking,SandboxCheckout,SandboxWebhookReceipt,SimulatedPayment,TestTicketReference,TestBoarding
from .test_booking import BookingFixture
from .sandbox_reconcile import reconcile
from .saspay import SasPayError

SECRET="sandbox-unit-test-secret"
HOOK="/api/v1/travel/webhooks/saspay/sandbox/"

@override_settings(DEBUG=True,SIRAGO_ENABLE_SIMULATED_PAYMENTS=True)
class SandboxIssuanceTests(BookingFixture,TestCase):
    def setUp(self):
        super().setUp()
        env=patch.dict("os.environ",{"SIRAGO_ENABLE_SASPAY_SANDBOX":"1","SIRAGO_ENABLE_SASPAY_TICKETS":"1","SASPAY_API_KEY":"sk_test_example","SIRAGO_ENV":"development","SASPAY_SANDBOX_WEBHOOK_SECRET":SECRET})
        env.start();self.addCleanup(env.stop)
        self.client.force_login(self.user)
        r=self.reserve()
        self.assertEqual(r.status_code,201,r.content)
        self.b=Booking.objects.get(pk=r.json()["id"])
        self.base=f"/api/v1/travel/bookings/{self.b.pk}/"
        self.a=SandboxCheckout.objects.create(booking=self.b,amount=16000,provider_id=uuid4(),status="PENDING",checkout_url="https://sandbox-checkout.saspay.me/example")
        self.txid=str(uuid4())
    def hook(self,stamp=None,signature=None,event="transaction.success",data=None):
        stamp=str(int(time.time()) if stamp is None else stamp)
        body=json.dumps({"event":event,"data":data if data is not None else {"id":self.txid,"type":"PAIEMENT","status":"SUCCESS","currency":"XOF","country":"ML","amount":"16000.00"}}).encode()
        sig=signature if signature is not None else hmac.new(SECRET.encode(),stamp.encode()+b"."+body,hashlib.sha256).hexdigest()
        return Client(enforce_csrf_checks=True).post(HOOK,body,content_type="application/json",HTTP_X_WEBHOOK_TIMESTAMP=stamp,HTTP_X_WEBHOOK_SIGNATURE=sig,HTTP_X_WEBHOOK_EVENT=event)
    def test_valid_webhook_is_durable_deduplicated_not_payment_authority(self):
        self.assertEqual(self.hook().status_code,202)
        self.assertEqual(self.hook().status_code,202)
        self.assertEqual(SandboxWebhookReceipt.objects.count(),1)
        self.assertFalse(TestTicketReference.objects.exists())
        self.assertIsNone(SandboxWebhookReceipt.objects.get().matched_at)
        with patch("fleet.sandbox_reconcile.inspect_booking_checkout",return_value=("PAID",self.txid)) as inspect:
            reconcile(self.a.pk)
            reconcile(self.a.pk)
            self.assertEqual(inspect.call_count,1)
        self.assertIsNotNone(SandboxWebhookReceipt.objects.get().matched_at)
        self.a.refresh_from_db();self.b.refresh_from_db()
        self.assertEqual(self.b.status,Booking.Status.TEST_PAID)
        self.assertIsNotNone(self.a.issued_at)
        self.assertEqual(str(self.a.transaction_id),self.txid)
        self.assertFalse(SimulatedPayment.objects.exists())
        self.assertEqual(TestTicketReference.objects.count(),1)
        notice = Notification.objects.get(recipient=self.user,kind="TEST_PAYMENT")
        self.assertEqual(notice.booking_id,self.b.pk)
        notices = self.client.get("/api/v1/auth/notifications/").json()["items"]
        self.assertEqual(next(n for n in notices if n["id"]==notice.id)["booking_id"],self.b.pk)
        self.client.force_login(self.other)
        other_notices = self.client.get("/api/v1/auth/notifications/").json()["items"]
        self.assertFalse(any(n["id"]==notice.id for n in other_notices))
        self.assertEqual(self.client.get(self.base+"tickets/0/0/pdf/").status_code,404)
        self.client.force_login(self.user)
    def test_reject_signature_timestamp_and_disabled(self):
        self.assertEqual(self.hook(signature="0"*64).status_code,403)
        self.assertEqual(self.hook(stamp=int(time.time())-301).status_code,403)
        self.assertEqual(self.hook(stamp=int(time.time())+301).status_code,403)
        with patch.dict("os.environ",{"SIRAGO_ENABLE_SASPAY_TICKETS":"0"}):
            self.assertEqual(self.hook().status_code,404)
        self.assertEqual(self.hook(event="webhook.test").status_code,200)
        self.assertFalse(SandboxWebhookReceipt.objects.exists())
    def test_manual_confirmation_qr_pdf_boarding_and_finance(self):
        with patch("fleet.sandbox_reconcile.inspect_booking_checkout",return_value=("PAID",self.txid)):
            r=self.client.post(self.base+"sandbox-checkout/verify/",{},content_type="application/json")
        self.assertEqual(r.status_code,200,r.content)
        self.assertEqual(r.json()["status"],"TEST_PAID")
        self.assertIsNone(r.json()["simulated_payment"])
        tickets=self.client.get(self.base+"tickets/").json()["items"]
        self.assertEqual(len(tickets),1)
        self.assertEqual(tickets[0]["count"],2)
        self.assertTrue(self.client.get(self.base+"tickets/0/0/pdf/").content.startswith(b"%PDF"))
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(self.base+"tickets/").status_code,404)
        self.client.force_login(self.owner)
        self.assertEqual(self.client.post("/api/v1/company/boarding/validate/",{"code":tickets[0]["code"],"passengers":[0,1]},content_type="application/json").status_code,200)
        self.assertEqual(TestBoarding.objects.count(),2)
        day=self.start.date().isoformat()
        m=self.client.get("/api/v1/company/finance/",{"date_from":day,"date_to":day}).json()["summary"]
        self.assertEqual((m["sandbox_amount"],m["simulated_amount"],m["real_amount"]),(16000,0,0))
    def test_individual_ticket_generation(self):
        Booking.objects.filter(pk=self.b.pk).update(ticket_mode="individual")
        with patch("fleet.sandbox_reconcile.inspect_booking_checkout",return_value=("PAID",self.txid)):
            reconcile(self.a.pk)
        self.assertEqual(TestTicketReference.objects.count(),2)
        self.assertEqual(len(self.client.get(self.base+"tickets/").json()["items"]),2)
    def test_expired_hold_never_reacquires_capacity(self):
        Booking.objects.filter(pk=self.b.pk).update(expires_at=timezone.now()-timedelta(seconds=1))
        with patch("fleet.sandbox_reconcile.inspect_booking_checkout",return_value=("PAID",self.txid)):
            reconcile(self.a.pk)
        self.a.refresh_from_db()
        self.assertEqual(self.a.status,"REVIEW_PAID")
        self.assertFalse(TestTicketReference.objects.exists())
        self.assertEqual(self.search()["total"],1)
    def test_provider_unavailable_never_issues(self):
        with patch("fleet.sandbox_reconcile.inspect_booking_checkout",side_effect=SasPayError("timeout")):
            self.assertRaises(SasPayError,reconcile,self.a.pk)
        self.a.refresh_from_db()
        self.assertEqual(self.a.status,"PENDING")
        self.assertFalse(TestTicketReference.objects.exists())
    def test_late_payment_never_issues(self):
        with patch("fleet.sandbox_reconcile.inspect_booking_checkout",return_value=("LATE_PAID",self.txid)):
            reconcile(self.a.pk)
        self.a.refresh_from_db()
        self.assertEqual(self.a.status,"LATE_PAID")
        self.assertFalse(TestTicketReference.objects.exists())
