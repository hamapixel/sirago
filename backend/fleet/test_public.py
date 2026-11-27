from datetime import timedelta
from django.test import TestCase
from django.utils import timezone
from accounts.models import Company,User
from .models import Bus,Route,Departure
from .views import TZ

class PublicSearchTests(TestCase):
    def setUp(self):
        u=User.objects.create_user(username="public-owner",role=User.Role.COMPANY)
        self.company=Company.objects.create(owner=u,name="Transport Test",city="Bamako",address="Gare",status=Company.Status.VERIFIED)
        self.bus=Bus.objects.create(company=self.company,name="Car 01",plate="AA 001",capacity=60)
        self.route=Route.objects.create(company=self.company,origin="Bamako",destination="Sikasso",boarding_point="Gare A",arrival_point="Gare B",duration_minutes=420,price=8000)
        self.start=(timezone.now().astimezone(TZ)+timedelta(days=1)).replace(hour=6,minute=0,second=0,microsecond=0)
        self.params={"origin":"Bamako","destination":"Sikasso","date":self.start.date().isoformat(),"passengers":1}
    def departure(self,**kw):
        values=dict(company=self.company,bus=self.bus,route=self.route,starts_at=self.start,ends_at=self.start+timedelta(hours=7),price=8000,capacity=60,status="PUBLISHED")
        values.update(kw)
        return Departure.objects.create(**values)
    def search(self,**kw):
        return self.client.get("/api/v1/travel/search/",{**self.params,**kw})
    def test_public_only_and_no_private_fields(self):
        d=self.departure()
        for s in ("DRAFT","CANCELLED","SUSPENDED"):
            self.departure(status=s)
        data=self.search().json()
        self.assertEqual(data["total"],1)
        self.assertEqual(data["items"][0]["id"],d.id)
        self.assertNotIn("plate",data["items"][0])
        self.assertNotIn("owner",data["items"][0])
    def test_unverified_or_inactive(self):
        self.departure()
        self.company.status="PENDING"
        self.company.save()
        self.assertEqual(self.search().json()["total"],0)
        self.company.status="VERIFIED"
        self.company.save()
        self.bus.active=False
        self.bus.save()
        self.assertEqual(self.search().json()["total"],0)
        self.bus.active=True
        self.bus.save()
        self.route.active=False
        self.route.save()
        self.assertEqual(self.search().json()["total"],0)
    def test_capacity_price_sort(self):
        self.departure(price=9000,capacity=3)
        cheaper=self.departure(price=7000,capacity=2)
        self.assertEqual(self.search().json()["items"][0]["id"],cheaper.id)
        self.assertEqual(self.search(passengers=3).json()["total"],1)
        self.assertEqual(self.search(max_price=7500).json()["total"],1)
        self.assertEqual(self.search(company="no match").json()["total"],0)
    def test_date_and_period(self):
        self.departure()
        self.departure(starts_at=self.start+timedelta(hours=12),ends_at=self.start+timedelta(hours=19))
        self.assertEqual(self.search(period="morning").json()["total"],1)
        self.assertEqual(self.search(period="evening").json()["total"],1)
        self.assertEqual(self.search(after=(self.start+timedelta(hours=7)).isoformat()).json()["total"],1)
        self.assertEqual(self.search(date=(self.start.date()+timedelta(days=1)).isoformat()).json()["total"],0)
    def test_invalid(self):
        for params in ({"origin":"Sikasso"},{"date":"bad"},{"passengers":101},{"sort":"bad"},{"page":0},{"after":"bad"}):
            self.assertEqual(self.search(**params).status_code,400)
    def test_home_real_data(self):
        self.departure(price=8500)
        self.departure(price=1000,status="DRAFT")
        data=self.client.get("/api/v1/travel/home/").json()
        self.assertEqual(data["routes"],[{"origin":"Bamako","destination":"Sikasso","price":8500}])
        self.assertEqual(data["companies"][0]["name"],self.company.name)
    def test_pagination(self):
        for i in range(21):
            self.departure(price=8000+i)
        self.assertEqual(len(self.search().json()["items"]),20)
        self.assertTrue(self.search().json()["has_next"])
        self.assertEqual(len(self.search(page=2).json()["items"]),1)
    def test_past_departure_today(self):
        now=timezone.now().astimezone(TZ)
        self.departure(starts_at=now-timedelta(minutes=1),ends_at=now+timedelta(hours=1))
        self.assertEqual(self.search(date=now.date().isoformat()).json()["total"],0)

    def test_company_choices_are_scoped_to_available_departures(self):
        self.bus.driver_first_name="Moussa"
        self.bus.driver_last_name="Diallo"
        self.bus.driver_phone="+22370123456"
        self.bus.save()
        self.departure()
        self.departure(status="SUSPENDED")
        self.departure(starts_at=self.start+timedelta(days=1),ends_at=self.start+timedelta(days=1,hours=7))
        owner=User.objects.create_user(username="second-public-owner",role=User.Role.COMPANY)
        second=Company.objects.create(owner=owner,name="Autre Transport",city="Bamako",address="Gare",status=Company.Status.VERIFIED)
        bus=Bus.objects.create(company=second,name="Car 02",plate="AA 002",capacity=60)
        route=Route.objects.create(company=second,origin="Bamako",destination="Sikasso",boarding_point="Gare A",arrival_point="Gare B",duration_minutes=420,price=8000)
        self.departure(company=second,bus=bus,route=route)
        data=self.search().json()
        self.assertEqual(data["total"],2)
        self.assertEqual({c["id"]:c["departures"] for c in data["companies"]},{self.company.pk:1,second.pk:1})
        data=self.search(company_id=second.pk).json()
        self.assertEqual(data["total"],1)
        self.assertEqual(data["items"][0]["company_id"],second.pk)
        self.assertEqual(len(data["companies"]),2)
        for item in self.search().json()["items"]:
            for key in ("driver_phone","driver_first_name","driver_last_name"):
                self.assertNotIn(key,item)

    def partner(self, **kw):
        return self.client.get(f"/api/v1/travel/partners/{self.company.pk}/",{"date":self.params["date"],**kw})

    def test_partner_only_eligible_departures(self):
        d=self.departure()
        self.departure(status="SUSPENDED")
        self.departure(status="DRAFT")
        self.departure(starts_at=self.start+timedelta(days=1),ends_at=self.start+timedelta(days=1,hours=7))
        r=self.partner()
        self.assertEqual(r.status_code,200,r.content)
        self.assertEqual(r.json()["company"],{"id":self.company.pk,"name":self.company.name,"city":self.company.city})
        self.assertEqual([row["id"] for row in r.json()["items"]],[d.pk])
        self.assertEqual(self.partner(q="SIK").json()["total"],1)
        self.assertEqual(self.partner(q="Kayes").json()["total"],0)
        self.assertEqual(self.partner(passengers=61).json()["total"],0)
        self.assertNotIn("driver_phone",r.json()["items"][0])
        self.assertNotIn("address",r.json()["company"])

    def test_partner_next_date_and_validation(self):
        self.departure()
        r=self.partner(date=timezone.now().astimezone(TZ).date().isoformat())
        self.assertEqual(r.json()["next_date"],self.params["date"])
        self.assertEqual(self.partner(passengers=0).status_code,400)
        self.assertEqual(self.partner(date="bad").status_code,400)
        self.assertEqual(self.partner(page=0).status_code,400)
        self.company.status=Company.Status.SUSPENDED
        self.company.save()
        self.assertEqual(self.partner().status_code,404)

    def test_partner_pagination(self):
        for i in range(21):
            self.departure(price=8000+i)
        r=self.partner().json()
        self.assertEqual((len(r["items"]),r["total"],r["has_next"]),(20,21,True))
        self.assertEqual(len(self.partner(page=2).json()["items"]),1)

    def test_partner_all_dates_default(self):
        a=self.departure()
        b=self.departure(starts_at=self.start+timedelta(days=2),ends_at=self.start+timedelta(days=2,hours=7))
        self.departure(status="SUSPENDED")
        r=self.partner(date="").json()
        self.assertEqual({t["id"] for t in r["items"]},{a.pk,b.pk})
        self.assertEqual(r["total"],2)
        self.assertIsNone(r["next_date"])

    def test_localities_seed_and_new_route_search(self):
        from .models import Locality
        self.assertEqual(Locality.objects.filter(kind="REGION").count(),19)
        self.assertTrue(Locality.objects.filter(name="Bamako",kind="DISTRICT").exists())
        self.assertTrue(Locality.objects.filter(name="Kati").exists())
        self.assertTrue(Locality.objects.filter(name="Kalabancoro").exists())
        self.route.destination="Gao"
        self.route.save()
        self.departure()
        self.assertEqual(self.search(destination="Gao").json()["total"],1)
        self.assertEqual(self.search(destination="Ville inconnue").status_code,400)

    def test_home_featured_real_departures_by_company_and_route(self):
        early=self.departure(price=8500)
        self.departure(starts_at=self.start+timedelta(hours=1),ends_at=self.start+timedelta(hours=8),price=7000)
        self.departure(status="DRAFT",price=1000)
        self.departure(starts_at=timezone.now()-timedelta(hours=1),ends_at=timezone.now()+timedelta(hours=6))
        self.departure(starts_at=self.start+timedelta(days=400),ends_at=self.start+timedelta(days=400,hours=7))
        owner=User.objects.create_user(username="featured-other",role=User.Role.COMPANY)
        second=Company.objects.create(owner=owner,name="Deuxième Transport",city="Bamako",address="Gare",status="VERIFIED")
        bus=Bus.objects.create(company=second,name="Car 02",plate="AA 002",capacity=60)
        route=Route.objects.create(company=second,origin="Bamako",destination="Sikasso",boarding_point="Gare A",arrival_point="Gare B",duration_minutes=420,price=8000)
        other=self.departure(company=second,bus=bus,route=route)
        result=self.client.get("/api/v1/travel/home/")
        self.assertEqual(result.status_code,200,result.content)
        rows=result.json()["departures"]
        self.assertEqual({x["id"] for x in rows},{early.pk,other.pk})
        first=next(x for x in rows if x["id"]==early.pk)
        self.assertEqual((first["company"],first["price"],first["duration_minutes"]),(self.company.name,8500,420))
        self.assertEqual(first["starts_at"],early.starts_at.isoformat())
        self.assertEqual(first["premium_remaining"],0)
        self.assertNotIn("plate",first)
        self.assertNotIn("owner",first)
        self.assertEqual(result.json()["company_logos"],{})
        second.status="SUSPENDED";second.save(update_fields=["status"])
        self.assertEqual([x["id"] for x in self.client.get("/api/v1/travel/home/").json()["departures"]],[early.pk])

    def test_public_search_reuses_group_counts_without_fetching_branding(self):
        from django.test import RequestFactory
        from django.test.utils import CaptureQueriesContext
        from django.db import connection
        from .public_views import search
        import json
        for i in range(21):
            self.departure(price=8000+i)
        self.company.logo="data:image/jpeg;base64,fixture"
        self.company.banner="data:image/jpeg;base64,fixture"
        self.company.save(update_fields=["logo","banner"])
        request=RequestFactory().get("/api/v1/travel/search/",{**self.params,"page":2})
        with CaptureQueriesContext(connection) as queries:
            response=search(request)
        self.assertEqual(response.status_code,200)
        body=json.loads(response.content)
        self.assertEqual((body["total"],len(body["items"]),body["has_next"]),(21,1,False))
        self.assertEqual(body["companies"][0]["departures"],21)
        self.assertEqual(len(queries),3)
        self.assertTrue(all('"logo"' not in q["sql"] and '"banner"' not in q["sql"] for q in queries))
        self.assertEqual(self.search(company="Transport").json()["total"],21)
        self.assertEqual(self.search(company_id=self.company.pk).json()["total"],21)

    def test_home_ranking_skips_full_departure_and_reacts_to_release(self):
        from uuid import uuid4
        from .models import Booking, BookingLeg
        early=self.departure(capacity=2,price=8000)
        same_time=self.departure(capacity=2,price=8500)
        later=self.departure(starts_at=self.start+timedelta(hours=1),
                             ends_at=self.start+timedelta(hours=8),price=7000)
        user=User.objects.create_user(username="home-rank-traveler")
        booking=Booking.objects.create(traveler=user,request_id=uuid4(),passengers=2,
            passenger_names=["Awa Test","Moussa Test"],status=Booking.Status.HELD,
            expires_at=timezone.now()+timedelta(minutes=10))
        BookingLeg.objects.create(booking=booking,departure=early,position=0,unit_price=8000)
        def home():
            response=self.client.get("/api/v1/travel/home/")
            self.assertEqual(response.status_code,200,response.content)
            self.assertIn("no-store",response["Cache-Control"])
            return response.json()
        body=home()
        self.assertEqual([r["id"] for r in body["departures"]],[same_time.pk])
        self.assertEqual(body["routes"][0]["price"],later.price)
        booking.expires_at=timezone.now()-timedelta(seconds=1)
        booking.save(update_fields=["expires_at"])
        self.assertEqual([r["id"] for r in home()["departures"]],[early.pk])
        self.company.status=Company.Status.SUSPENDED
        self.company.save(update_fields=["status"])
        body=home()
        self.assertEqual((body["departures"],body["companies"],body["routes"]),([],[],[]))

    def test_home_ranking_limits_global_results_and_keeps_distinct_city_pairs(self):
        from .models import Locality
        Locality.objects.get_or_create(name="Kayes",defaults={"kind":"REGION"})
        first=self.departure()
        route=Route.objects.create(company=self.company,origin="Bamako",destination="Kayes",
            boarding_point="Gare A",arrival_point="Gare C",duration_minutes=420,price=8000)
        second=self.departure(route=route)
        for i in range(12):
            owner=User.objects.create_user(username=f"home-rank-owner-{i}",role=User.Role.COMPANY)
            company=Company.objects.create(owner=owner,name=f"Home rank {i}",city="Bamako",
                address="Gare",status=Company.Status.VERIFIED)
            bus=Bus.objects.create(company=company,name="Car",plate=f"HOME {i}",capacity=60)
            other_route=Route.objects.create(company=company,origin="Bamako",destination="Sikasso",
                boarding_point="Gare A",arrival_point="Gare B",duration_minutes=420,price=8000)
            self.departure(company=company,bus=bus,route=other_route,
                starts_at=self.start+timedelta(hours=i+1),ends_at=self.start+timedelta(hours=i+8))
        body=self.client.get("/api/v1/travel/home/").json()
        self.assertEqual(len(body["departures"]),12)
        self.assertEqual([d["id"] for d in body["departures"][:2]],[first.pk,second.pk])
        self.assertEqual(len(body["companies"]),13)
        self.assertEqual(len(body["routes"]),2)

    def test_verified_partners_and_uploaded_logo_without_departure(self):
        import base64
        from io import BytesIO
        from PIL import Image
        buf=BytesIO()
        Image.new("RGB",(2,2),"green").save(buf,format="JPEG")
        image=buf.getvalue()
        self.company.logo="data:image/jpeg;base64,"+base64.b64encode(image).decode("ascii")
        self.company.save(update_fields=["logo"])
        owner=User.objects.create_user(username="pending-partner",role=User.Role.COMPANY)
        pending=Company.objects.create(owner=owner,name="Pending Transport",city="Bamako",address="Private",
                                       status=Company.Status.PENDING,logo=self.company.logo)
        def home():
            return self.client.get("/api/v1/travel/home/").json()
        body=home()
        url=f"/api/v1/travel/partners/{self.company.pk}/logo/"
        self.assertEqual(body["departures"],[])
        self.assertEqual(body["companies"],[{"id":self.company.pk,"name":self.company.name,
                         "city":self.company.city,"logo_url":url}])
        response=self.client.get(url)
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.content,image)
        self.assertEqual(response["Content-Type"],"image/jpeg")
        self.assertIn("no-store",response["Cache-Control"])
        self.assertEqual(self.client.get(f"/api/v1/travel/partners/{pending.pk}/logo/").status_code,404)
        pending.status=Company.Status.VERIFIED
        pending.save(update_fields=["status"])
        self.assertEqual({x["id"] for x in home()["companies"]},{self.company.pk,pending.pk})
        self.company.status=Company.Status.SUSPENDED
        self.company.save(update_fields=["status"])
        self.assertEqual(self.client.get(url).status_code,404)
        self.assertEqual([x["id"] for x in home()["companies"]],[pending.pk])

    def test_partner_directory_pagination(self):
        for i in range(30):
            user=User.objects.create_user(username=f"directory-{i}",role=User.Role.COMPANY)
            Company.objects.create(owner=user,name=f"Directory {i:02d}",city="Bamako",address="Gare",
                                   status=Company.Status.VERIFIED)
        first=self.client.get("/api/v1/travel/home/").json()
        second=self.client.get("/api/v1/travel/home/",{"partner_page":2}).json()
        self.assertEqual((len(first["companies"]),len(second["companies"])),(30,1))
        self.assertTrue(first["partners_has_next"])
        self.assertFalse(second["partners_has_next"])
        self.assertFalse({x["id"] for x in first["companies"]}&{x["id"] for x in second["companies"]})
        self.assertEqual(self.client.get("/api/v1/travel/home/",{"partner_page":0}).status_code,400)
