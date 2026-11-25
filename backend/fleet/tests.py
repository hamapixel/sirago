from datetime import timedelta
from django.test import TestCase, Client
from django.utils import timezone
from accounts.models import Company,User
from .models import Bus,Route,Departure

class FleetTests(TestCase):
    def setUp(self):
        self.user=User.objects.create_user(username="owner",role=User.Role.COMPANY)
        self.company=Company.objects.create(owner=self.user,name="Demo",city="Bamako",address="Gare")
        self.other=User.objects.create_user(username="other",role=User.Role.COMPANY)
        self.other_company=Company.objects.create(owner=self.other,name="Other",city="Bamako",address="Gare",status=Company.Status.VERIFIED)
        self.bus=Bus.objects.create(company=self.company,name="Car 01",plate="AA 001",capacity=60)
        self.route=Route.objects.create(company=self.company,origin="Bamako",destination="Sikasso",boarding_point="Gare A",arrival_point="Gare B",duration_minutes=420,price=8000)
        self.date=(timezone.localdate()+timedelta(days=1)).isoformat()
        self.payload={"bus_id":self.bus.id,"route_id":self.route.id,"date":self.date,"time":"06:00","capacity":60,"price":8000}
        self.client.force_login(self.user)
    def post(self,path,data):
        return self.client.post("/api/v1/company/"+path+"/",data,content_type="application/json")
    def create_departure(self):
        response=self.post("departures",self.payload)
        self.assertEqual(response.status_code,201,response.content)
        return Departure.objects.get()
    def verify(self):
        self.company.status=Company.Status.VERIFIED
        self.company.save()
    def test_create_bus(self):
        self.assertEqual(self.post("buses",{"name":"Car 02","plate":"aa 002","capacity":50}).status_code,201)
        self.assertEqual(self.post("buses",{"name":"duplicate","plate":"AA 002","capacity":50}).status_code,409)
        self.assertEqual(self.post("buses",{"name":"bad","plate":"A","capacity":0}).status_code,400)
    def test_route(self):
        v={"origin":"Bamako","destination":"Bamako","boarding_point":"A","arrival_point":"B","duration_minutes":60,"price":1000}
        self.assertEqual(self.post("routes",v).status_code,400)
        self.assertEqual(self.post("routes",{**v,"destination":"Kayes"}).status_code,201)
    def test_pending_publish_then_verified(self):
        d=self.create_departure()
        self.assertEqual(self.post(f"departures/{d.id}/status",{"status":"PUBLISHED"}).status_code,403)
        self.verify()
        self.assertEqual(self.post(f"departures/{d.id}/status",{"status":"PUBLISHED"}).status_code,200)
        d.refresh_from_db()
        self.assertEqual(d.status,"PUBLISHED")
    def test_capacity_and_overlap(self):
        self.assertEqual(self.post("departures",{**self.payload,"capacity":61}).status_code,400)
        self.create_departure()
        self.assertEqual(self.post("departures",{**self.payload,"time":"07:00"}).status_code,409)
        self.assertEqual(Departure.objects.count(),1)
    def test_daily_series_atomic(self):
        self.create_departure()
        end=(timezone.localdate()+timedelta(days=3)).isoformat()
        self.assertEqual(self.post("departures",{**self.payload,"frequency":"daily","end_date":end}).status_code,409)
        self.assertEqual(Departure.objects.count(),1)
        self.assertEqual(self.post("departures",{**self.payload,"time":"15:00","frequency":"daily","end_date":end}).status_code,201)
        self.assertEqual(Departure.objects.count(),4)
    def test_isolation(self):
        d=self.create_departure()
        self.client.force_login(self.other)
        self.assertEqual(self.client.get("/api/v1/company/buses/").json()["items"],[])
        self.assertEqual(self.post(f"buses/{self.bus.id}",{"name":"steal","plate":"X","capacity":60}).status_code,404)
        self.assertEqual(self.post("departures",self.payload).status_code,404)
        self.assertEqual(self.post(f"departures/{d.id}/status",{"status":"CANCELLED"}).status_code,404)
    def test_suspended_and_traveler(self):
        self.company.status=Company.Status.SUSPENDED
        self.company.save()
        self.assertEqual(self.post("departures",self.payload).status_code,403)
        traveler=User.objects.create_user(username="traveler")
        self.client.force_login(traveler)
        self.assertEqual(self.client.get("/api/v1/company/buses/").status_code,403)
        self.client.logout()
        self.assertEqual(self.client.get("/api/v1/company/buses/").status_code,401)
    def test_csrf_and_active_departure(self):
        self.create_departure()
        self.assertEqual(self.post(f"buses/{self.bus.id}",{"name":"Car 01","plate":"AA 001","capacity":59}).status_code,409)
        client=Client(enforce_csrf_checks=True)
        client.force_login(self.user)
        self.assertEqual(client.post("/api/v1/company/buses/",{"name":"X","plate":"X","capacity":50},content_type="application/json").status_code,403)
    def test_cancel_and_edit(self):
        d=self.create_departure()
        self.assertEqual(self.post(f"departures/{d.id}",{**self.payload,"price":8500}).status_code,200)
        self.assertEqual(self.post(f"departures/{d.id}/status",{"status":"CANCELLED"}).status_code,200)
        self.assertEqual(self.post(f"departures/{d.id}/status",{"status":"PUBLISHED"}).status_code,409)
        self.assertEqual(self.post("departures",self.payload).status_code,201)
