from datetime import timedelta
from django.test import TestCase,Client,override_settings
from accounts.models import Notification
from .models import Booking,Departure,TestTicketReport,TestTicketReference
from .test_booking import BookingFixture
from .availability import with_remaining
from django.utils import timezone

@override_settings(DEBUG=True,SIRAGO_ENABLE_SIMULATED_PAYMENTS=True)
class ReportTests(BookingFixture,TestCase):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.user)
        r=self.reserve()
        self.assertEqual(r.status_code,201,r.content)
        self.original=r.json()["id"]
        self.base=f"/api/v1/travel/bookings/{self.original}/"
        self.assertEqual(self.client.post(self.base+"simulate-payment/",{"network":"orange_ml"},content_type="application/json").status_code,200)
        self.code=self.client.get(self.base+"tickets/").json()["items"][0]["code"]
        self.target=Departure.objects.create(company=self.company,bus=self.departure.bus,route=self.departure.route,starts_at=self.start+timedelta(days=1),ends_at=self.start+timedelta(days=1,hours=7),price=9000,capacity=2,status="PUBLISHED")
    def report(self,**kwargs):
        return self.client.post(self.base+"report/",{"departure_id":self.target.pk,"total":18000,**kwargs},content_type="application/json")
    def test_report_inventory_qr_and_retry(self):
        options=self.client.get(self.base+"report/options/").json()
        self.assertEqual(options["items"][0]["difference"],2000)
        r=self.report()
        self.assertEqual(r.status_code,201,r.content)
        new=r.json()
        self.assertEqual(new["total"],18000)
        self.assertEqual(new["passenger_names"],self.payload["passenger_names"])
        self.assertEqual(new["ticket_mode"],"group")
        self.assertEqual(self.report().json()["id"],new["id"])
        self.assertEqual(TestTicketReport.objects.count(),1)
        self.assertEqual(Booking.objects.get(pk=self.original).status,"REPORTED")
        self.assertEqual(self.client.get(self.base).json()["replacement_id"],new["id"])
        self.assertEqual(self.client.get(self.base+"tickets/").status_code,409)
        self.assertEqual(self.client.get(self.base+"tickets/0/0/pdf/").status_code,409)
        self.assertTrue(TestTicketReference.objects.filter(code=self.code).exists())
        code=self.client.get(f'/api/v1/travel/bookings/{new["id"]}/tickets/').json()["items"][0]["code"]
        self.assertNotEqual(code,self.code)
        rows={d.pk:d.remaining for d in with_remaining(Departure.objects.all(),timezone.now())}
        self.assertEqual(rows[self.departure.pk],2)
        self.assertEqual(rows[self.target.pk],0)
        self.assertEqual(Notification.objects.filter(kind="TEST_REPORT").count(),2)
        self.client.force_login(self.owner)
        url="/api/v1/company/boarding/lookup/"
        self.assertEqual(self.client.post(url,{"code":self.code},content_type="application/json").status_code,404)
        self.assertEqual(self.client.post(url,{"code":code},content_type="application/json").status_code,200)
    def test_wrong_price_and_unavailable_preserve_original(self):
        self.assertEqual(self.report(total=1).status_code,409)
        self.target.status="SUSPENDED";self.target.save(update_fields=["status"])
        self.assertEqual(self.report().status_code,409)
        self.assertEqual(Booking.objects.get(pk=self.original).status,"TEST_PAID")
        self.assertEqual(TestTicketReport.objects.count(),0)
        self.assertEqual(self.client.get(self.base+"tickets/").status_code,200)
    def test_boarded_passenger_blocks_report(self):
        self.client.force_login(self.owner)
        self.assertEqual(self.client.post("/api/v1/company/boarding/validate/",{"code":self.code,"passengers":[0]},content_type="application/json").status_code,200)
        self.client.force_login(self.user)
        self.assertEqual(self.report().status_code,409)
        self.assertEqual(self.client.get(self.base+"report/options/").status_code,409)
        self.assertEqual(Booking.objects.get(pk=self.original).status,"TEST_PAID")
    def test_access_and_production_disabled(self):
        self.client.force_login(self.other)
        self.assertEqual(self.report().status_code,404)
        self.assertEqual(self.client.get(self.base+"report/options/").status_code,404)
        self.client.force_login(self.owner)
        self.assertEqual(self.report().status_code,403)
        self.client.force_login(self.user)
        c=Client(enforce_csrf_checks=True);c.force_login(self.user)
        self.assertEqual(c.post(self.base+"report/",{"departure_id":self.target.pk,"total":18000},content_type="application/json").status_code,403)
        with override_settings(DEBUG=False):
            self.assertEqual(self.report().status_code,404)
