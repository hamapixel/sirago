from django.test import TestCase, Client
from django.core.cache import cache
from .models import User, Company

class AuthTests(TestCase):
    def setUp(self):
        cache.clear()
        self.payload = {"first_name":"Moussa","last_name":"Coulibaly","phone":"70000001","email":"demo@example.com","password":"Fleuve!2026-Ciel","password_confirmation":"Fleuve!2026-Ciel","terms":True}

    def post(self, path, values):
        return self.client.post("/api/v1/auth/"+path+"/", values, content_type="application/json")

    def test_traveler_register_and_session(self):
        result = self.post("register/traveler", {**self.payload,"role":"ADMIN","is_superuser":True})
        self.assertEqual(result.status_code,201)
        user = User.objects.get(phone="+22370000001")
        self.assertFalse(user.is_superuser)
        self.assertTrue(user.check_password(self.payload["password"]))
        self.assertEqual(self.client.get("/api/v1/auth/me/").json()["role"],"TRAVELER")
        self.assertEqual(self.client.get("/api/v1/auth/company/").status_code,403)

    def test_company_pending(self):
        result = self.post("register/company",{**self.payload,"company_name":"Transport Test","city":"Bamako","address":"Gare test","status":"VERIFIED"})
        self.assertEqual(result.status_code,201)
        self.assertEqual(Company.objects.get().status,"PENDING")
        self.assertEqual(self.client.get("/api/v1/auth/company/").json()["name"],"Transport Test")

    def test_duplicates_and_login(self):
        self.assertEqual(self.post("register/traveler",self.payload).status_code,201)
        self.post("logout",{})
        self.assertEqual(self.post("register/traveler",{**self.payload,"email":"other@example.com"}).status_code,409)
        self.assertEqual(self.post("register/traveler",{**self.payload,"phone":"70000002","email":"DEMO@EXAMPLE.COM"}).status_code,409)
        self.assertEqual(self.post("login",{"identifier":"70000001","password":"wrong"}).status_code,401)
        self.assertEqual(self.post("login",{"identifier":"DEMO@EXAMPLE.COM","password":self.payload["password"]}).status_code,200)
        self.post("logout",{})
        self.assertEqual(self.client.get("/api/v1/auth/me/").status_code,401)
        self.assertEqual(self.post("login",{"identifier":"+22370000001","password":self.payload["password"]}).status_code,200)

    def test_invalid_registration(self):
        self.assertEqual(self.post("register/traveler",{**self.payload,"terms":False}).status_code,400)
        self.assertEqual(self.post("register/traveler",{**self.payload,"phone":"bad"}).status_code,400)
        self.assertEqual(self.post("register/company",self.payload).status_code,400)
        self.assertEqual(User.objects.count(),0)

    def test_csrf(self):
        client = Client(enforce_csrf_checks=True)
        self.assertEqual(client.post("/api/v1/auth/register/traveler/",self.payload,content_type="application/json").status_code,403)
        token = client.get("/api/v1/auth/csrf/").json()["csrfToken"]
        self.assertEqual(client.post("/api/v1/auth/register/traveler/",self.payload,content_type="application/json",HTTP_X_CSRFTOKEN=token).status_code,201)

    def test_rate_limit(self):
        for _ in range(20):
            self.post("login",{"identifier":"bad","password":"bad"})
        self.assertEqual(self.post("login",{"identifier":"bad","password":"bad"}).status_code,429)
