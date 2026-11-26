from datetime import timedelta
from unittest.mock import patch
from django.test import TestCase, override_settings
from django.utils import timezone
from .models import Booking, SandboxCheckout, SimulatedPayment, TestTicketReference
from .test_booking import BookingFixture
from .saspay import SasPayError, create_booking_checkout, verify_booking_checkout, checkout_booking_reference

SID="c9a17e2c-4b1a-4f0e-9c3d-2a1b3c4d5e6f"
URL="https://sandbox-checkout.saspay.me/checkout/example"

@override_settings(DEBUG=True,SIRAGO_ENABLE_SIMULATED_PAYMENTS=True)
class BookingCheckoutTests(BookingFixture,TestCase):
    def setUp(self):
        super().setUp()
        env=patch.dict("os.environ",{"SIRAGO_ENABLE_SASPAY_SANDBOX":"1","SIRAGO_ENABLE_SASPAY_TICKETS":"0","SASPAY_API_KEY":"sk_test_example","SIRAGO_ENV":"development"})
        env.start();self.addCleanup(env.stop)
        self.client.force_login(self.user)
        r=self.reserve()
        self.assertEqual(r.status_code,201,r.content)
        self.b=Booking.objects.get(pk=r.json()["id"])
        self.base=f"/api/v1/travel/bookings/{self.b.pk}/"
    def post(self,path):
        return self.client.post(self.base+path,{},content_type="application/json")
    @patch("fleet.sandbox_views.create_booking_checkout",return_value=(SID,URL))
    def test_create_once_and_frozen_total(self,mock):
        r=self.post("sandbox-checkout/")
        self.assertEqual(r.status_code,201,r.content)
        self.assertEqual(r.json()["sandbox_checkout"]["amount"],16000)
        self.assertEqual(r.json()["sandbox_checkout"]["checkout_url"],URL)
        self.assertEqual(self.post("sandbox-checkout/").status_code,200)
        self.assertEqual(mock.call_count,1)
        self.assertEqual(mock.call_args.args[2],16000)
        self.assertEqual(self.post("cancel/").status_code,409)
        self.assertEqual(self.client.post(self.base+"simulate-payment/",{"network":"orange_ml"},content_type="application/json").status_code,409)
    @patch("fleet.sandbox_views.create_booking_checkout",side_effect=SasPayError("timeout"))
    def test_ambiguous_creation_never_retries(self,mock):
        self.assertEqual(self.post("sandbox-checkout/").status_code,502)
        self.assertEqual(self.post("sandbox-checkout/").json()["sandbox_checkout"]["status"],"UNKNOWN")
        self.assertEqual(mock.call_count,1)
    @patch("fleet.sandbox_views.verify_booking_checkout",return_value="PAID")
    @patch("fleet.sandbox_views.create_booking_checkout",return_value=(SID,URL))
    def test_paid_no_ticket_no_real_receipt(self,create,verify):
        self.assertEqual(self.post("sandbox-checkout/").status_code,201)
        r=self.post("sandbox-checkout/verify/")
        self.assertEqual(r.status_code,200,r.content)
        self.assertEqual(r.json()["sandbox_checkout"]["status"],"PAID")
        self.assertEqual(r.json()["status"],"HELD")
        self.assertFalse(SimulatedPayment.objects.exists())
        self.assertFalse(TestTicketReference.objects.exists())
        self.assertEqual(self.post("sandbox-checkout/verify/").status_code,200)
        self.assertEqual(verify.call_count,1)
    @patch("fleet.sandbox_views.create_booking_checkout")
    def test_ownership_expiration_and_disabled_flag(self,mock):
        self.client.force_login(self.other)
        self.assertEqual(self.post("sandbox-checkout/").status_code,404)
        self.client.force_login(self.user)
        with patch.dict("os.environ",{"SIRAGO_ENABLE_SASPAY_SANDBOX":"0"}):
            self.assertEqual(self.post("sandbox-checkout/").status_code,404)
        Booking.objects.filter(pk=self.b.pk).update(expires_at=timezone.now()-timedelta(seconds=1))
        self.assertEqual(self.post("sandbox-checkout/").status_code,409)
        mock.assert_not_called()
    @patch("fleet.saspay._checkout_request")
    def test_provider_contract_and_late_payment(self,request):
        value={"id":SID,"checkout_url":URL,"amount":"16000.00","currency":"XOF","country":"ML","status":"PENDING","metadata":{"sirago_reference":checkout_booking_reference(self.b)},"expires_at":self.b.expires_at.isoformat()}
        request.return_value=value
        self.assertEqual(create_booking_checkout("sk_test_example",self.b,16000),(SID,URL))
        for changed in ({"amount":"1.00"},{"currency":"USD"},{"metadata":{}},{"expires_at":None},{"checkout_url":"https://pay.saspay.me/checkout/x"}):
            request.return_value={**value,**changed}
            with self.assertRaises(SasPayError):create_booking_checkout("sk_test_example",self.b,16000)
        a=SandboxCheckout.objects.create(booking=self.b,amount=16000,provider_id=SID,checkout_url=URL,status="PENDING")
        request.side_effect=[{**value,"status":"PAID","paid_at":(self.b.expires_at+timedelta(seconds=1)).isoformat()},{"id":SID,"status":"PAID","transaction_status":"SUCCESS","transaction_id":SID}]
        self.assertEqual(verify_booking_checkout("sk_test_example",self.b,a),"LATE_PAID")
