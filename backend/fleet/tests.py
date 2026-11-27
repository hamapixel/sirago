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
    def test_premium_capacity_and_tariff(self):
        self.assertEqual(self.post("buses",{"name":"Bad","plate":"BAD","capacity":5,"premium_capacity":5}).status_code,400)
        self.assertEqual(self.post(f"buses/{self.bus.id}",{"name":"Car 01","plate":"AA 001","capacity":60,"premium_capacity":10}).status_code,200)
        self.assertEqual(self.post("departures",{**self.payload,"premium_capacity":11,"premium_price":12000}).status_code,400)
        self.assertEqual(self.post("departures",{**self.payload,"premium_capacity":5,"premium_price":12000}).status_code,400)
        self.assertEqual(self.post("departures",{**self.payload,"premium_capacity":10,"premium_price":7000}).status_code,400)
        response=self.post("departures",{**self.payload,"premium_capacity":10,"premium_price":12000})
        self.assertEqual(response.status_code,201,response.content)
        d=Departure.objects.get()
        self.assertEqual((d.premium_capacity,d.premium_price),(10,12000))
        self.assertEqual(self.post(f"buses/{self.bus.id}",{"name":"Car 01","plate":"AA 001","capacity":60,"premium_capacity":5}).status_code,409)
        row=self.client.get("/api/v1/company/departures/").json()["items"][0]
        self.assertEqual((row["standard_remaining"],row["premium_remaining"]),(50,10))

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
    def test_bus_capacity_lock_and_driver_update(self):
        self.verify()
        path = f"buses/{self.bus.id}"
        values = {"name":"Car 01","plate":"AA 001","capacity":60,"premium_capacity":0,"active":True}
        self.assertFalse(self.client.get("/api/v1/company/buses/").json()["items"][0]["capacity_locked"])
        departure = self.create_departure()
        self.assertEqual(self.post(f"departures/{departure.id}/status",{"status":"PUBLISHED"}).status_code,200)
        self.assertTrue(self.client.get("/api/v1/company/buses/").json()["items"][0]["capacity_locked"])
        result = self.post(path,{**values,"driver_first_name":"Adama","driver_last_name":"Traore","driver_phone":"76123456"})
        self.assertEqual(result.status_code,200,result.content)
        self.assertTrue(result.json()["capacity_locked"])
        self.assertEqual(result.json()["driver_phone"],"+22376123456")
        self.assertEqual(self.post(path,{**values,"premium_capacity":10}).status_code,409)
        self.assertEqual(self.post(path,{**values,"active":False}).status_code,409)
        self.assertEqual(self.post(f"departures/{departure.id}/status",{"status":"CANCELLED"}).status_code,200)
        self.assertFalse(self.client.get("/api/v1/company/buses/").json()["items"][0]["capacity_locked"])
        self.assertEqual(self.post(path,{**values,"premium_capacity":10}).status_code,200)

    def test_cancel_and_edit(self):
        d=self.create_departure()
        self.assertEqual(self.post(f"departures/{d.id}",{**self.payload,"price":8500}).status_code,200)
        self.assertEqual(self.post(f"departures/{d.id}/status",{"status":"CANCELLED"}).status_code,200)
        self.assertEqual(self.post(f"departures/{d.id}/status",{"status":"PUBLISHED"}).status_code,409)
        self.assertEqual(self.post("departures",self.payload).status_code,201)

    def test_publish_batch_verified(self):
        d=self.create_departure()
        end=(timezone.localdate()+timedelta(days=2)).isoformat()
        result=self.post("departures",{**self.payload,"date":end})
        self.assertEqual(result.status_code,201)
        ids=list(Departure.objects.values_list("id",flat=True))
        self.assertEqual(self.post("departures/publish-batch",{"ids":ids}).status_code,403)
        self.verify()
        response=self.post("departures/publish-batch",{"ids":ids})
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.json()["published"],2)
        self.assertEqual(Departure.objects.filter(status="PUBLISHED").count(),2)

    def test_batch_atomic_and_owner_scoped(self):
        d=self.create_departure()
        self.verify()
        self.assertEqual(self.post("departures/publish-batch",{"ids":[d.id,d.id]}).status_code,400)
        self.assertEqual(self.post("departures/publish-batch",{"ids":[d.id,d.id+1000]}).status_code,404)
        self.client.force_login(self.other)
        self.assertEqual(self.post("departures/publish-batch",{"ids":[d.id]}).status_code,404)
        d.refresh_from_db()
        self.assertEqual(d.status,"DRAFT")
        self.client.force_login(self.user)
        end=(timezone.localdate()+timedelta(days=2)).isoformat()
        self.assertEqual(self.post("departures",{**self.payload,"date":end}).status_code,201)
        second=Departure.objects.exclude(pk=d.pk).get()
        second.status="CANCELLED"
        second.save(update_fields=["status"])
        self.assertEqual(self.post("departures/publish-batch",{"ids":[d.id,second.id]}).status_code,409)
        d.refresh_from_db()
        self.assertEqual(d.status,"DRAFT")

    def test_batch_rejects_past_departure(self):
        d=self.create_departure()
        self.verify()
        d.starts_at=timezone.now()-timedelta(hours=8)
        d.ends_at=timezone.now()-timedelta(hours=1)
        d.save(update_fields=["starts_at","ends_at"])
        self.assertEqual(self.post("departures/publish-batch",{"ids":[d.id]}).status_code,409)

    def test_departure_filters(self):
        d=self.create_departure()
        self.verify()
        self.post(f"departures/{d.id}/status",{"status":"PUBLISHED"})
        end=(timezone.localdate()+timedelta(days=2)).isoformat()
        self.assertEqual(self.post("departures",{**self.payload,"date":end}).status_code,201)
        url="/api/v1/company/departures/"
        response=self.client.get(url,{"status":"PUBLISHED","route_id":self.route.id,"date_from":self.date,"date_to":self.date})
        self.assertEqual([x["id"] for x in response.json()["items"]],[d.id])
        self.assertEqual(self.client.get(url,{"status":"DRAFT","date_to":self.date}).json()["items"],[])
        self.assertEqual(self.client.get(url,{"route_id":self.route.id+1000}).json()["items"],[])
        self.assertEqual(self.client.get(url,{"date_from":end,"date_to":self.date}).status_code,400)
        self.assertEqual(self.client.get(url,{"status":"invalid"}).status_code,400)
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(url,{"route_id":self.route.id}).json()["items"],[])

    def test_batch_csrf(self):
        d=self.create_departure()
        self.verify()
        client=Client(enforce_csrf_checks=True)
        client.force_login(self.user)
        response=client.post("/api/v1/company/departures/publish-batch/",{"ids":[d.id]},content_type="application/json")
        self.assertEqual(response.status_code,403)

    def test_driver_information_private_and_editable(self):
        v={"name":"Car 02","plate":"AA 002","capacity":50,"premium_capacity":0,"driver_first_name":"Moussa","driver_last_name":"Diallo","driver_phone":"70 12 34 56"}
        r=self.post("buses",v)
        self.assertEqual(r.status_code,201,r.content)
        b=Bus.objects.get(pk=r.json()["id"])
        self.assertEqual((b.driver_first_name,b.driver_last_name,b.driver_phone),("Moussa","Diallo","+22370123456"))
        self.assertEqual(self.post("buses",{**v,"plate":"AA 003","driver_phone":"123"}).status_code,400)
        self.assertEqual(self.post("buses",{**v,"plate":"AA 003","driver_last_name":""}).status_code,400)
        self.assertEqual(self.post(f"buses/{b.pk}",{"name":"Car 02 modifié","plate":"AA 002","capacity":50}).status_code,200)
        b.refresh_from_db()
        self.assertEqual(b.driver_phone,"+22370123456")
        self.assertEqual(self.post(f"buses/{b.pk}",{**v,"driver_first_name":"","driver_last_name":"","driver_phone":""}).status_code,200)
        b.refresh_from_db()
        self.assertEqual(b.driver_phone,"")
        self.client.force_login(self.other)
        self.assertEqual(self.client.get("/api/v1/company/buses/").json()["items"],[])
    def test_batch_suspend_reactivate(self):
        d=self.create_departure()
        self.verify()
        self.assertEqual(self.post(f"departures/{d.pk}/status",{"status":"PUBLISHED"}).status_code,200)
        self.assertEqual(self.post("departures/publish-batch",{"ids":[d.pk],"status":"SUSPENDED"}).status_code,200)
        d.refresh_from_db()
        self.assertEqual(d.status,"SUSPENDED")
        self.assertEqual(self.post("departures/publish-batch",{"ids":[d.pk],"status":"PUBLISHED"}).status_code,200)
        d.refresh_from_db()
        self.assertEqual(d.status,"PUBLISHED")
        self.assertEqual(self.post("departures/publish-batch",{"ids":[d.pk],"status":"CANCELLED"}).status_code,400)
        d.starts_at=timezone.now()-timedelta(hours=2)
        d.save(update_fields=["starts_at"])
        self.assertEqual(self.post("departures/publish-batch",{"ids":[d.pk],"status":"SUSPENDED"}).status_code,409)
