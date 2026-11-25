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
