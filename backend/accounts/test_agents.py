from django.test import TestCase,Client
from django.core.cache import cache
from .models import Company,CompanyAgent,User

class AgentTests(TestCase):
    def setUp(self):
        cache.clear()
        self.owner=User.objects.create_user(username="owner",role=User.Role.COMPANY)
        self.company=Company.objects.create(owner=self.owner,name="Transport",city="Bamako",address="Gare",status="VERIFIED")
        self.client.force_login(self.owner)
        self.url="/api/v1/auth/company/agents/"
        self.payload={"first_name":"Awa","last_name":"Test","phone":"70000002","email":"","role":"CONTROLLER","password":"Fleuve!Agent2026","password_confirmation":"Fleuve!Agent2026"}
    def post(self,url,values):
        return self.client.post(url,values,content_type="application/json")
    def create(self):
        r=self.post(self.url,self.payload)
        self.assertEqual(r.status_code,201,r.content)
        return CompanyAgent.objects.get(pk=r.json()["id"])
    def test_creation_and_login(self):
        a=self.create()
        self.assertTrue(a.user.check_password(self.payload["password"]))
        self.assertNotIn("password",self.client.get(self.url).json()["items"][0])
        self.client.logout()
        r=self.post("/api/v1/auth/login/",{"identifier":"70000002","password":self.payload["password"]})
        self.assertEqual(r.status_code,200,r.content)
        self.assertEqual(r.json()["company_role"],"CONTROLLER")
        self.assertEqual(r.json()["company"]["name"],self.company.name)
        self.assertEqual(self.client.get(self.url).status_code,403)
        self.assertEqual(self.post(self.url,self.payload).status_code,403)
    def test_disable_revokes_session_and_reenable(self):
        a=self.create()
        agent=Client()
        agent.force_login(a.user)
        self.assertEqual(self.post(self.url+str(a.pk)+"/",{"action":"disable"}).status_code,200)
        self.assertEqual(agent.get("/api/v1/auth/me/").status_code,401)
        self.assertEqual(self.post(self.url+str(a.pk)+"/",{"action":"enable","password":"Nouveau!Agent2026","password_confirmation":"Nouveau!Agent2026"}).status_code,200)
        self.assertEqual(agent.get("/api/v1/auth/me/").status_code,401)
        a.user.refresh_from_db()
        self.assertTrue(a.user.check_password("Nouveau!Agent2026"))
        self.assertFalse(a.user.check_password(self.payload["password"]))
    def test_other_company_and_duplicate(self):
        a=self.create()
        self.assertEqual(self.post(self.url,self.payload).status_code,409)
        other=User.objects.create_user(username="other",role=User.Role.COMPANY)
        Company.objects.create(owner=other,name="Autre",city="Bamako",address="Gare",status="VERIFIED")
        self.client.force_login(other)
        self.assertEqual(self.client.get(self.url).json()["items"],[])
        self.assertEqual(self.post(self.url+str(a.pk)+"/",{"action":"disable"}).status_code,404)
    def test_role_change_and_csrf(self):
        a=self.create()
        self.assertEqual(self.post(self.url+str(a.pk)+"/",{"action":"role","role":"CLERK"}).status_code,200)
        a.refresh_from_db()
        self.assertEqual(a.role,"CLERK")
        self.assertEqual(self.post(self.url+str(a.pk)+"/",{"action":"role","role":"OWNER"}).status_code,400)
        c=Client(enforce_csrf_checks=True)
        c.force_login(self.owner)
        self.assertEqual(c.post(self.url,self.payload,content_type="application/json").status_code,403)
