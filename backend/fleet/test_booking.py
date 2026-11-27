from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier
from uuid import uuid4
from django.db import connection, connections
from django.test import TestCase, TransactionTestCase, Client
from django.utils import timezone
from accounts.models import Company, User
from .models import Bus, Route, Departure, Booking, Locality
from .views import TZ

class BookingFixture:
    def setUp(self):
        # TransactionTestCase flushes migration-seeded data between tests.
        Locality.objects.get_or_create(name="Bamako", defaults={"kind": "DISTRICT"})
        Locality.objects.get_or_create(name="Sikasso", defaults={"kind": "REGION"})
        owner=User.objects.create_user(username="booking-owner",role=User.Role.COMPANY)
        self.owner=owner
        self.company=Company.objects.create(owner=owner,name="Transport Test",city="Bamako",address="Gare",status="VERIFIED")
        bus=Bus.objects.create(company=self.company,name="Car 01",plate="AA 001",capacity=2)
        route=Route.objects.create(company=self.company,origin="Bamako",destination="Sikasso",boarding_point="Gare A",arrival_point="Gare B",duration_minutes=420,price=8000)
        self.start=(timezone.now().astimezone(TZ)+timedelta(days=1)).replace(hour=6,minute=0,second=0,microsecond=0)
        self.departure=Departure.objects.create(company=self.company,bus=bus,route=route,starts_at=self.start,ends_at=self.start+timedelta(hours=7),price=8000,capacity=2,status="PUBLISHED")
        self.user=User.objects.create_user(username="traveler1",role=User.Role.TRAVELER)
        self.other=User.objects.create_user(username="traveler2",role=User.Role.TRAVELER)
        self.payload={"out":self.departure.pk,"count":2,"passenger_names":["Awa Test","Moussa Test"],"total":16000,"request_id":str(uuid4())}
        self.url="/api/v1/travel/bookings/reserve/"
    def reserve(self,client=None,**kw):
        return (client or self.client).post(self.url,{**self.payload,**kw},content_type="application/json")
    def search(self):
        response = self.client.get("/api/v1/travel/search/", {"origin": "Bamako", "destination": "Sikasso", "date": self.start.date().isoformat(), "passengers": 1})
        self.assertEqual(response.status_code, 200, response.content)
        return response.json()

class BookingTests(BookingFixture,TestCase):
    def test_guest_can_quote_not_reserve(self):
        self.assertEqual(self.client.get("/api/v1/travel/quote/",{"out":self.departure.id,"count":2}).json()["total"],16000)
        self.assertEqual(self.reserve().status_code,401)
    def test_company_cannot_reserve(self):
        self.client.force_login(self.owner)
        self.assertEqual(self.reserve().status_code,403)
    def test_inventory_and_idempotency(self):
        self.client.force_login(self.user)
        result=self.reserve()
        self.assertEqual(result.status_code,201,result.content)
        self.assertEqual(self.reserve().status_code,200)
        self.assertEqual(Booking.objects.count(),1)
        self.assertEqual(self.search()["total"],0)
        self.client.force_login(self.other)
        self.assertEqual(self.reserve(request_id=str(uuid4())).status_code,409)
    def test_cancel_releases_and_is_private(self):
        self.client.force_login(self.user)
        b=self.reserve().json()
        self.client.force_login(self.other)
        self.assertEqual(self.client.get("/api/v1/travel/bookings/").json()["items"],[])
        url=f"/api/v1/travel/bookings/{b['id']}/cancel/"
        self.assertEqual(self.client.post(url).status_code,404)
        self.client.force_login(self.user)
        self.assertEqual(self.client.post(url).status_code,200)
        self.assertEqual(self.search()["items"][0]["remaining"],2)
    def test_expiry_releases(self):
        self.client.force_login(self.user)
        self.assertEqual(self.reserve().status_code,201)
        Booking.objects.update(expires_at=timezone.now()-timedelta(seconds=1))
        self.assertEqual(self.search()["items"][0]["remaining"],2)
        self.assertEqual(self.client.get("/api/v1/travel/bookings/").json()["items"][0]["status"],"EXPIRED")
    def test_price_and_status_rechecked(self):
        self.client.force_login(self.user)
        self.assertEqual(self.reserve(total=1).status_code,409)
        self.departure.status="SUSPENDED"
        self.departure.save()
        self.assertEqual(self.reserve().status_code,409)
        self.assertEqual(Booking.objects.count(),0)
    def test_return_atomic(self):
        self.client.force_login(self.user)
        self.assertEqual(self.reserve(ret=self.departure.id+1000,total=32000).status_code,409)
        self.assertEqual(Booking.objects.count(),0)
        route=Route.objects.create(company=self.company,origin="Sikasso",destination="Bamako",boarding_point="B",arrival_point="A",duration_minutes=420,price=7000)
        ret=Departure.objects.create(company=self.company,bus=self.departure.bus,route=route,starts_at=self.start+timedelta(hours=8),ends_at=self.start+timedelta(hours=15),price=7000,capacity=2,status="PUBLISHED")
        result=self.reserve(ret=ret.id,total=30000)
        self.assertEqual(result.status_code,201,result.content)
        self.assertEqual(len(result.json()["trips"]),2)
    def test_company_cannot_cancel_held_departure(self):
        self.client.force_login(self.user)
        self.assertEqual(self.reserve().status_code,201)
        self.client.force_login(self.owner)
        url=f"/api/v1/company/departures/{self.departure.id}/status/"
        self.assertEqual(self.client.post(url,{"status":"CANCELLED"},content_type="application/json").status_code,409)
        self.assertEqual(len(self.client.get("/api/v1/company/reservations/").json()["items"]),1)
    def test_detail_owner_and_frozen_price(self):
        self.client.force_login(self.user)
        b=self.reserve().json()
        self.departure.price=9000
        self.departure.save(update_fields=["price"])
        url=f"/api/v1/travel/bookings/{b['id']}/"
        response=self.client.get(url)
        self.assertEqual(response.status_code,200)
        detail=response.json()
        self.assertEqual(detail["total"],16000)
        self.assertEqual(detail["trips"][0]["price"],8000)
        self.assertEqual(detail["trips"][0]["boarding_point"],"Gare A")
        self.assertEqual(detail["trips"][0]["arrival_point"],"Gare B")
        self.assertEqual(detail["trips"][0]["bus_name"],"Car 01")
        self.assertIn("ends_at",detail["trips"][0])
        self.assertIn("created_at",detail)
        self.assertNotIn("plate",detail["trips"][0])
        self.assertIn("no-store",response["Cache-Control"])
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(url).status_code,404)
        self.client.force_login(self.owner)
        self.assertEqual(self.client.get(url).status_code,403)
        self.client.logout()
        self.assertEqual(self.client.get(url).status_code,401)

    def test_detail_expired_and_cancelled(self):
        self.client.force_login(self.user)
        b=self.reserve().json()
        url=f"/api/v1/travel/bookings/{b['id']}/"
        Booking.objects.filter(pk=b["id"]).update(expires_at=timezone.now()-timedelta(seconds=1))
        self.assertEqual(self.client.get(url).json()["status"],"EXPIRED")
        self.assertEqual(self.client.post(url+"cancel/").json()["status"],"EXPIRED")
        fresh=self.reserve(request_id=str(uuid4())).json()
        url=f"/api/v1/travel/bookings/{fresh['id']}/"
        self.assertEqual(self.client.post(url+"cancel/").status_code,200)
        self.assertEqual(self.client.get(url).json()["status"],"CANCELLED")

    def test_detail_invalid_id(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.get("/api/v1/travel/bookings/99999999999999999999/").status_code,404)

    def test_passenger_names_saved_and_private(self):
        self.client.force_login(self.user)
        result=self.reserve(passenger_names=["  Awa   Test ", "Awa Test"])
        self.assertEqual(result.status_code,201,result.content)
        b=result.json()
        self.assertEqual(b["passenger_names"],["Awa Test","Awa Test"])
        self.assertEqual(Booking.objects.get(pk=b["id"]).passenger_names,b["passenger_names"])
        self.assertEqual(self.reserve(passenger_names=["Awa Test","Awa Test"]).status_code,200)
        self.assertEqual(self.reserve().status_code,409)
        self.client.force_login(self.owner)
        self.assertNotIn("passenger_names",self.client.get("/api/v1/company/reservations/").json()["items"][0])

    def test_invalid_passenger_names_do_not_hold_seats(self):
        self.client.force_login(self.user)
        for names in (None, [], ["Awa Test"], ["Awa Test",""], ["Awa Test",42], ["Awa Test","9"], ["Awa Test","A"*101]):
            self.assertEqual(self.reserve(passenger_names=names).status_code,409)
        self.assertEqual(Booking.objects.count(),0)
        self.assertEqual(self.search()["items"][0]["remaining"],2)

    def test_legacy_booking_without_names_remains_readable(self):
        self.client.force_login(self.user)
        b=self.reserve().json()
        Booking.objects.filter(pk=b["id"]).update(passenger_names=[])
        self.assertEqual(self.client.get(f"/api/v1/travel/bookings/{b['id']}/").json()["passenger_names"],[])

    def test_mixed_categories_inventory_and_cancel(self):
        bus=self.departure.bus
        bus.premium_capacity=1
        bus.save()
        self.departure.premium_capacity=1
        self.departure.premium_price=12000
        self.departure.save()
        self.client.force_login(self.user)
        self.assertEqual(self.reserve().status_code,409)
        self.assertEqual(self.reserve(premium_positions=[[1]],total=16000).status_code,409)
        response=self.reserve(premium_positions=[[1]],total=20000)
        self.assertEqual(response.status_code,201,response.content)
        b=response.json()
        self.assertEqual(b["total"],20000)
        self.assertEqual(b["trips"][0]["premium_positions"],[1])
        self.assertEqual(self.reserve(premium_positions=[[1]],total=20000).status_code,200)
        self.assertEqual(self.search()["total"],0)
        self.client.post(f"/api/v1/travel/bookings/{b['id']}/cancel/")
        row=self.search()["items"][0]
        self.assertEqual((row["standard_remaining"],row["premium_remaining"]),(1,1))

    def test_premium_only_remaining_search_and_quote(self):
        bus=self.departure.bus
        bus.premium_capacity=1
        bus.save()
        self.departure.premium_capacity=1
        self.departure.premium_price=12000
        self.departure.save()
        self.client.force_login(self.user)
        self.assertEqual(self.reserve(count=1,passenger_names=["Awa Test"],total=8000).status_code,201)
        row=self.search()["items"][0]
        self.assertEqual((row["standard_remaining"],row["premium_remaining"],row["from_price"]),(0,1,12000))
        q=self.client.get("/api/v1/travel/quote/",{"out":self.departure.id,"count":1}).json()
        self.assertEqual(q["total"],12000)
        self.client.force_login(self.other)
        self.assertEqual(self.reserve(count=1,passenger_names=["Moussa Test"],premium_positions=[[0]],total=12000).status_code,201)

    def test_return_different_categories_and_expiry(self):
        bus=self.departure.bus
        bus.premium_capacity=1
        bus.save()
        self.departure.capacity=1
        self.departure.save()
        route=Route.objects.create(company=self.company,origin="Sikasso",destination="Bamako",boarding_point="B",arrival_point="A",duration_minutes=420,price=7000)
        ret=Departure.objects.create(company=self.company,bus=bus,route=route,starts_at=self.start+timedelta(hours=8),ends_at=self.start+timedelta(hours=15),price=7000,capacity=2,premium_capacity=1,premium_price=11000,status="PUBLISHED")
        self.client.force_login(self.user)
        response=self.reserve(count=1,passenger_names=["Awa Test"],ret=ret.id,premium_positions=[[],[0]],total=19000)
        self.assertEqual(response.status_code,201,response.content)
        b=response.json()
        self.assertEqual([t["total"] for t in b["trips"]],[8000,11000])
        from .availability import with_remaining
        row=with_remaining(Departure.objects.filter(pk=ret.pk),timezone.now()).get()
        self.assertEqual((row.standard_remaining,row.premium_remaining),(1,0))
        Booking.objects.filter(pk=b["id"]).update(expires_at=timezone.now()-timedelta(seconds=1))
        row=with_remaining(Departure.objects.filter(pk=ret.pk),timezone.now()).get()
        self.assertEqual((row.standard_remaining,row.premium_remaining),(1,1))

    def test_public_search_rejects_inconsistent_physical_capacity(self):
        self.assertEqual(self.search()["total"],1)
        bus=self.departure.bus
        bus.premium_capacity=1
        bus.save()
        # Two Standard seats cannot be offered when the bus has one.
        self.assertEqual(self.search()["total"],0)
        self.departure.premium_capacity=1
        self.departure.premium_price=12000
        self.departure.save()
        self.assertEqual(self.search()["total"],1)
        bus.premium_capacity=0
        bus.save()
        self.assertEqual(self.search()["total"],0)

    def test_invalid_category_selection(self):
        self.client.force_login(self.user)
        for positions in ([[0,0]],[[2]],[[True]],["premium"],[[],[]]):
            self.assertEqual(self.reserve(premium_positions=positions).status_code,409)
        self.assertEqual(Booking.objects.count(),0)

    def test_csrf(self):
        client=Client(enforce_csrf_checks=True)
        client.force_login(self.user)
        self.assertEqual(self.reserve(client).status_code,403)

class ConcurrentBookingTests(BookingFixture,TransactionTestCase):
    def test_last_seats(self):
        if connection.vendor!="postgresql":
            self.skipTest("PostgreSQL row locks required")
        clients=[Client(),Client()]
        clients[0].force_login(self.user)
        clients[1].force_login(self.other)
        barrier=Barrier(2)
        def run(client):
            try:
                barrier.wait(timeout=10)
                return self.reserve(client,request_id=str(uuid4())).status_code
            finally:
                connections.close_all()
        with ThreadPoolExecutor(max_workers=2) as executor:
            results=list(executor.map(run,clients))
        self.assertEqual(sorted(results),[201,409])
        self.assertEqual(Booking.objects.count(),1)

    def test_parallel_retry_creates_only_one_booking(self):
        if connection.vendor != "postgresql":
            self.skipTest("PostgreSQL row locks required")
        clients = [Client(), Client()]
        for client in clients:
            client.force_login(self.user)
        barrier = Barrier(2)

        def run(client):
            try:
                barrier.wait(timeout=10)
                response = self.reserve(client)
                return response.status_code, response.json().get("id")
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(run, clients))
        self.assertEqual(sorted(code for code, _ in results), [200, 201])
        self.assertEqual(Booking.objects.count(), 1)
        booking = Booking.objects.get()
        self.assertEqual({pk for _, pk in results}, {booking.pk})
        self.assertEqual(booking.legs.count(), 1)
        self.assertEqual(self.search()["total"], 0)

    def test_parallel_reservations_cannot_oversell_premium(self):
        if connection.vendor != "postgresql":
            self.skipTest("PostgreSQL row locks required")
        bus = self.departure.bus
        bus.premium_capacity = 1
        bus.save(update_fields=["premium_capacity"])
        self.departure.premium_capacity = 1
        self.departure.premium_price = 12000
        self.departure.save(update_fields=["premium_capacity", "premium_price"])
        clients = [Client(), Client()]
        clients[0].force_login(self.user)
        clients[1].force_login(self.other)
        barrier = Barrier(2)

        def run(client):
            try:
                barrier.wait(timeout=10)
                return self.reserve(
                    client, count=1, passenger_names=["Awa Test"],
                    premium_positions=[[0]], total=12000,
                    request_id=str(uuid4()),
                ).status_code
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(run, clients))
        self.assertEqual(sorted(results), [201, 409])
        self.assertEqual(Booking.objects.count(), 1)
        from .availability import with_remaining
        departure = with_remaining(
            Departure.objects.filter(pk=self.departure.pk), timezone.now()
        ).get()
        self.assertEqual((departure.standard_remaining, departure.premium_remaining), (1, 0))

    def test_twenty_travelers_compete_for_ten_seats(self):
        if connection.vendor != "postgresql":
            self.skipTest("PostgreSQL row locks required")
        from .availability import with_remaining

        bus = self.departure.bus
        bus.capacity = 10
        bus.premium_capacity = 4
        bus.save(update_fields=["capacity", "premium_capacity"])
        self.departure.capacity = 10
        self.departure.premium_capacity = 4
        self.departure.premium_price = 12000
        self.departure.save(update_fields=["capacity", "premium_capacity", "premium_price"])
        attempts = []
        for i in range(20):
            user = User.objects.create_user(username=f"seat-race-{i}", role=User.Role.TRAVELER)
            client = Client()
            client.force_login(user)
            premium = i >= 10
            payload = dict(count=1, passenger_names=["Awa Test"],
                           premium_positions=[[0]] if premium else [[]],
                           total=12000 if premium else 8000,
                           request_id=str(uuid4()))
            attempts.append((client, premium, payload))

        barrier = Barrier(len(attempts))

        def run(attempt):
            client, premium, payload = attempt
            try:
                barrier.wait(timeout=30)
                response = self.reserve(client, **payload)
                return response.status_code, premium, response.json().get("id")
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=len(attempts)) as executor:
            results = list(executor.map(run, attempts))

        self.assertEqual(sorted(code for code, _, _ in results), [201]*10 + [409]*10)
        self.assertEqual(sum(code == 201 and premium for code, premium, _ in results), 4)
        self.assertEqual(sum(code == 201 and not premium for code, premium, _ in results), 6)
        self.assertEqual(Booking.objects.count(), 10)
        self.assertEqual(Booking.objects.filter(status=Booking.Status.HELD).count(), 10)
        self.assertEqual(len({pk for code, _, pk in results if code == 201}), 10)
        departure = with_remaining(
            Departure.objects.filter(pk=self.departure.pk), timezone.now()
        ).get()
        self.assertEqual((departure.remaining, departure.standard_remaining,
                          departure.premium_remaining), (0, 0, 0))

        # A repeated successful request returns the same booking without
        # consuming a second seat; a cancellation releases the correct class.
        index = next(i for i, result in enumerate(results) if result[0] == 201 and result[1])
        client, _, payload = attempts[index]
        booking_id = results[index][2]
        retry = self.reserve(client, **payload)
        self.assertEqual(retry.status_code, 200)
        self.assertEqual(retry.json()["id"], booking_id)
        self.assertEqual(Booking.objects.count(), 10)
        self.assertEqual(client.post(f"/api/v1/travel/bookings/{booking_id}/cancel/").status_code, 200)
        departure = with_remaining(
            Departure.objects.filter(pk=self.departure.pk), timezone.now()
        ).get()
        self.assertEqual((departure.remaining, departure.standard_remaining,
                          departure.premium_remaining), (1, 0, 1))
        index = next(i for i, result in enumerate(results) if result[0] == 409 and result[1])
        client, _, payload = attempts[index]
        self.assertEqual(self.reserve(client, **payload).status_code, 201)
        self.assertEqual(Booking.objects.filter(status=Booking.Status.HELD).count(), 10)
        departure = with_remaining(
            Departure.objects.filter(pk=self.departure.pk), timezone.now()
        ).get()
        self.assertEqual((departure.remaining, departure.standard_remaining,
                          departure.premium_remaining), (0, 0, 0))
