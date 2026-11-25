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

    def test_partial_keeps_other_passenger_and_reissues_both(self):
        options=self.client.get(self.base+"report/options/",{"passengers":"1"}).json()
        self.assertEqual(options["previous_amount"],8000)
        self.assertEqual(options["items"][0]["difference"],1000)
        r=self.report(passengers=[1],total=9000)
        self.assertEqual(r.status_code,201,r.content)
        new=r.json()
        retained=new["retained_booking"]
        self.assertEqual(new["passenger_names"],["Moussa Test"])
        self.assertEqual(retained["passenger_names"],["Awa Test"])
        self.assertEqual(retained["total"],8000)
        self.assertEqual(self.report(passengers=[1],total=9000).json()["retained_booking"]["id"],retained["id"])
        self.assertEqual(self.report(passengers=[0],total=9000).status_code,409)
        self.assertEqual(TestTicketReport.objects.count(),1)
        self.assertEqual(self.client.get(self.base).json()["retained_id"],retained["id"])
        rows={d.pk:d.remaining for d in with_remaining(Departure.objects.all(),timezone.now())}
        self.assertEqual((rows[self.departure.pk],rows[self.target.pk]),(1,1))
        self.assertEqual(self.client.get(self.base+"tickets/").status_code,409)
        codes=[self.client.get(f'/api/v1/travel/bookings/{b["id"]}/tickets/').json()["items"][0]["code"] for b in (new,retained)]
        self.assertEqual(len(set([self.code,*codes])),3)
        self.client.force_login(self.owner)
        url="/api/v1/company/boarding/lookup/"
        self.assertEqual(self.client.post(url,{"code":self.code},content_type="application/json").status_code,404)
        for code in codes:
            self.assertEqual(self.client.post(url,{"code":code},content_type="application/json").status_code,200)

    def test_partial_invalid_selection_and_suspended_original(self):
        for invalid in ([],[0,0],[2],[True],"0"):
            self.assertEqual(self.report(passengers=invalid,total=9000).status_code,409)
        self.departure.status="SUSPENDED";self.departure.save(update_fields=["status"])
        self.assertEqual(self.report(passengers=[0],total=9000).status_code,409)
        self.assertEqual(Booking.objects.get(pk=self.original).status,"TEST_PAID")
        self.assertEqual(TestTicketReport.objects.count(),0)

    def test_partial_preserves_premium_and_identical_names(self):
        from .models import BookingLeg,SimulatedPayment
        from .ticket_refs import register_refs
        # Prepare an existing paid reservation with a standard and a premium passenger.
        bus=self.departure.bus
        bus.premium_capacity=1;bus.save(update_fields=["premium_capacity"])
        for d,price in ((self.departure,12000),(self.target,13000)):
            d.premium_capacity=1;d.premium_price=price;d.save(update_fields=["premium_capacity","premium_price"])
        b=Booking.objects.get(pk=self.original)
        b.passenger_names=["Awa Test","Awa Test"];b.save(update_fields=["passenger_names"])
        leg=b.legs.get()
        leg.premium_count=1;leg.premium_positions=[1];leg.premium_unit_price=12000
        leg.save(update_fields=["premium_count","premium_positions","premium_unit_price"])
        SimulatedPayment.objects.filter(booking=b).update(amount=20000)
        TestTicketReference.objects.filter(leg=leg).delete()
        register_refs(b,[leg])
        r=self.report(passengers=[1],total=13000)
        self.assertEqual(r.status_code,201,r.content)
        new=r.json()
        self.assertEqual(new["trips"][0]["premium_positions"],[0])
        self.assertEqual(new["retained_booking"]["trips"][0]["premium_positions"],[])
        self.assertEqual(new["retained_booking"]["total"],8000)
        self.assertEqual(TestTicketReport.objects.get().previous_amount,12000)


@override_settings(DEBUG=True,SIRAGO_ENABLE_SIMULATED_PAYMENTS=True)
class RoundReportTests(BookingFixture,TestCase):
    def setUp(self):
        super().setUp()
        from .models import Route
        route=Route.objects.create(company=self.company,origin="Sikasso",destination="Bamako",boarding_point="Gare B",arrival_point="Gare A",duration_minutes=420,price=7000)
        def departure(route,start,price):
            return Departure.objects.create(company=self.company,bus=self.departure.bus,route=route,starts_at=start,ends_at=start+timedelta(hours=7),price=price,capacity=2,status="PUBLISHED")
        self.ret=departure(route,self.start+timedelta(days=3),7000)
        self.new_ret=departure(route,self.start+timedelta(days=4),9000)
        self.new_out=departure(self.departure.route,self.start+timedelta(days=1),9000)
        self.late_out=departure(self.departure.route,self.start+timedelta(days=5),9000)
        self.early_ret=departure(route,self.start+timedelta(hours=1),9000)
        self.client.force_login(self.user)
        r=self.reserve(ret=self.ret.pk,total=30000)
        self.assertEqual(r.status_code,201,r.content)
        self.base=f'/api/v1/travel/bookings/{r.json()["id"]}/'
        self.original=r.json()["id"]
        self.assertEqual(self.client.post(self.base+"simulate-payment/",{"network":"orange_ml"},content_type="application/json").status_code,200)
        self.codes=[t["code"] for t in self.client.get(self.base+"tickets/").json()["items"]]
    def move(self,leg,departure,amount,**kw):
        return self.client.post(self.base+"report/",{"leg":leg,"departure_id":departure.pk,"total":amount,**kw},content_type="application/json")
    def test_return_only_preserves_outbound_and_invalidates_old_codes(self):
        opts=self.client.get(self.base+"report/options/",{"leg":1}).json()
        self.assertEqual(opts["previous_amount"],14000)
        self.assertIn(self.new_ret.pk,[x["id"] for x in opts["items"]])
        self.assertNotIn(self.early_ret.pk,[x["id"] for x in opts["items"]])
        r=self.move(1,self.new_ret,18000)
        self.assertEqual(r.status_code,201,r.content)
        b=r.json()
        self.assertEqual([x["id"] for x in b["trips"]],[self.departure.pk,self.new_ret.pk])
        self.assertEqual(b["total"],34000)
        self.assertEqual(b["simulated_payment"]["amount"],34000)
        self.assertEqual(self.move(1,self.new_ret,18000).json()["id"],b["id"])
        self.assertEqual(self.move(0,self.departure,18000).status_code,409)
        self.assertEqual(self.client.get(self.base+"tickets/").status_code,409)
        new_codes=[t["code"] for t in self.client.get(f'/api/v1/travel/bookings/{b["id"]}/tickets/').json()["items"]]
        self.assertFalse(set(new_codes)&set(self.codes))
        self.client.force_login(self.owner)
        for code in self.codes:
            self.assertEqual(self.client.post("/api/v1/company/boarding/lookup/",{"code":code},content_type="application/json").status_code,404)
    def test_partial_outbound_preserves_both_groups_return(self):
        r=self.move(0,self.new_out,9000,passengers=[1])
        self.assertEqual(r.status_code,201,r.content)
        b=r.json();kept=b["retained_booking"]
        self.assertEqual([x["id"] for x in b["trips"]],[self.new_out.pk,self.ret.pk])
        self.assertEqual([x["id"] for x in kept["trips"]],[self.departure.pk,self.ret.pk])
        self.assertEqual((b["total"],kept["total"]),(16000,15000))
        rows={d.pk:d.remaining for d in with_remaining(Departure.objects.all(),timezone.now())}
        self.assertEqual((rows[self.departure.pk],rows[self.new_out.pk],rows[self.ret.pk]),(1,1,0))
    def test_incompatible_departures_preserve_original(self):
        self.assertEqual(self.move(0,self.late_out,18000).status_code,409)
        self.assertEqual(self.move(1,self.early_ret,18000).status_code,409)
        self.assertEqual(self.move(2,self.new_ret,18000).status_code,400)
        self.assertEqual(Booking.objects.get(pk=self.original).status,"TEST_PAID")
        self.assertEqual(TestTicketReport.objects.count(),0)
    def test_started_outbound_blocks_return_report(self):
        now=timezone.now()
        Departure.objects.filter(pk=self.departure.pk).update(starts_at=now-timedelta(hours=1),ends_at=now+timedelta(hours=6))
        self.assertEqual(self.move(1,self.new_ret,18000).status_code,409)
        self.assertEqual(self.client.get(self.base+"report/options/",{"leg":1}).status_code,409)
