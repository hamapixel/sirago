from datetime import timedelta
from django.test import TestCase, override_settings, Client
from django.utils import timezone
from .test_booking import BookingFixture
from .models import Booking, SimulatedPayment

@override_settings(DEBUG=True,SIRAGO_ENABLE_SIMULATED_PAYMENTS=True)
class SimulatedPaymentTests(BookingFixture,TestCase):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.user)
        result=self.reserve()
        self.assertEqual(result.status_code,201)
        self.pk=result.json()["id"]
        self.pay_url=f"/api/v1/travel/bookings/{self.pk}/simulate-payment/"

    def pay(self,network="orange_ml",**kwargs):
        return self.client.post(self.pay_url,{"network":network,**kwargs},content_type="application/json")

    def test_server_amount_and_idempotency(self):
        result=self.pay(amount=1)
        self.assertEqual(result.status_code,200,result.content)
        self.assertEqual(result.json()["status"],"TEST_PAID")
        self.assertEqual(result.json()["simulated_payment"]["amount"],16000)
        self.assertEqual(self.pay().status_code,200)
        self.assertEqual(SimulatedPayment.objects.count(),1)

    def test_expiration_and_cancel_do_not_release_test_paid(self):
        self.assertEqual(self.pay().status_code,200)
        Booking.objects.filter(pk=self.pk).update(expires_at=timezone.now()-timedelta(seconds=1))
        self.assertEqual(self.search()["total"],0)
        self.assertEqual(self.client.post(f"/api/v1/travel/bookings/{self.pk}/cancel/").json()["status"],"TEST_PAID")

    def test_reject_expired_and_cancelled(self):
        Booking.objects.filter(pk=self.pk).update(expires_at=timezone.now()-timedelta(seconds=1))
        self.assertEqual(self.pay().status_code,409)
        Booking.objects.filter(pk=self.pk).update(status="CANCELLED")
        self.assertEqual(self.pay().status_code,409)
        self.assertFalse(SimulatedPayment.objects.exists())

    def test_disabled_even_if_flag_on_in_production(self):
        with override_settings(DEBUG=False):
            self.assertEqual(self.pay().status_code,404)
        with override_settings(SIRAGO_ENABLE_SIMULATED_PAYMENTS=False):
            self.assertEqual(self.pay().status_code,404)
        self.assertFalse(SimulatedPayment.objects.exists())

    def test_ownership_and_authentication(self):
        self.client.force_login(self.other)
        self.assertEqual(self.pay().status_code,404)
        self.client.force_login(self.owner)
        self.assertEqual(self.pay().status_code,403)
        self.client.logout()
        self.assertEqual(self.pay().status_code,401)

    def test_csrf_required(self):
        client=Client(enforce_csrf_checks=True)
        client.force_login(self.user)
        self.assertEqual(client.post(self.pay_url,{"network":"orange_ml"},content_type="application/json").status_code,403)

    def test_invalid_network_and_unavailable_departure(self):
        self.assertEqual(self.pay(network="invalid").status_code,400)
        self.departure.status="SUSPENDED"
        self.departure.save(update_fields=["status"])
        self.assertEqual(self.pay().status_code,409)
        self.assertFalse(SimulatedPayment.objects.exists())

    def test_company_cannot_cancel_after_simulation(self):
        self.assertEqual(self.pay(network="moov_ml").status_code,200)
        self.client.force_login(self.owner)
        self.assertEqual(self.client.post(f"/api/v1/company/departures/{self.departure.pk}/status/",{"status":"CANCELLED"},content_type="application/json").status_code,409)
        self.assertEqual(self.client.get("/api/v1/company/reservations/").json()["items"][0]["status"],"TEST_PAID")
