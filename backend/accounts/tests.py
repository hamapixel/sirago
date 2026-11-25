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

    def test_profile_update_is_self_only_and_preserves_identifiers(self):
        self.assertEqual(self.post("register/traveler", self.payload).status_code, 201)
        other = User.objects.create_user(username="other", first_name="Other")
        response = self.post("profile", {"first_name":" Awa  Marie ", "last_name":"Traoré", "phone":"+22370000002", "email":"other@example.com", "role":"ADMIN", "id":other.pk})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["first_name"], "Awa Marie")
        user=User.objects.get(phone="+22370000001")
        self.assertEqual(user.last_name, "Traoré")
        self.assertEqual(user.email, self.payload["email"])
        self.assertEqual(user.role, User.Role.TRAVELER)
        other.refresh_from_db()
        self.assertEqual(other.first_name, "Other")
        self.assertIn("no-store", response["Cache-Control"])

    def test_profile_validation_and_access(self):
        self.assertEqual(self.post("profile",{}).status_code,401)
        self.assertEqual(self.post("password",{}).status_code,401)
        self.post("register/traveler",self.payload)
        for payload in ({"first_name":"","last_name":"Test"},{"first_name":"A"*151,"last_name":"Test"},{"first_name":42,"last_name":"Test"}):
            self.assertEqual(self.post("profile",payload).status_code,400)
        self.post("logout",{})
        self.post("register/company",{**self.payload,"phone":"70000002","email":"company@example.com","company_name":"Test","city":"Bamako","address":"Gare"})
        self.assertEqual(self.post("profile",{}).status_code,403)
        self.assertEqual(self.post("password",{}).status_code,403)
        admin=User.objects.create_superuser(username="admin",password="Demo!Strong2026")
        self.client.force_login(admin)
        self.assertEqual(self.post("profile",{}).status_code,403)
        self.assertEqual(self.post("password",{}).status_code,403)

    def test_profile_password_changes_and_keeps_current_session(self):
        self.post("register/traveler", self.payload)
        new="Nouveau!Fleuve2026"
        values={"current_password":self.payload["password"],"password":new,"password_confirmation":new}
        self.assertEqual(self.post("password",{**values,"current_password":"wrong"}).status_code,400)
        self.assertEqual(self.post("password",{**values,"password_confirmation":"different"}).status_code,400)
        self.assertEqual(self.post("password",{**values,"password":"12345678","password_confirmation":"12345678"}).status_code,400)
        self.assertEqual(self.post("password",values).status_code,200)
        self.assertEqual(self.client.get("/api/v1/auth/me/").status_code,200)
        self.post("logout",{})
        self.assertEqual(self.post("login",{"identifier":self.payload["phone"],"password":self.payload["password"]}).status_code,401)
        self.assertEqual(self.post("login",{"identifier":self.payload["phone"],"password":new}).status_code,200)

    def test_profile_mutations_require_csrf(self):
        self.post("register/traveler", self.payload)
        user=User.objects.get(phone="+22370000001")
        client=Client(enforce_csrf_checks=True)
        client.force_login(user)
        for path in ("profile","password"):
            self.assertEqual(client.post("/api/v1/auth/"+path+"/",{},content_type="application/json").status_code,403)

    def test_password_change_rate_limit(self):
        self.post("register/traveler",self.payload)
        for _ in range(10):
            self.assertEqual(self.post("password",{}).status_code,400)
        self.assertEqual(self.post("password",{}).status_code,429)


    def test_company_profile_and_password(self):
        self.assertEqual(self.post("company/profile",{}).status_code,401)
        self.assertEqual(self.post("register/company",{**self.payload,"company_name":"Transport Test","city":"Bamako","address":"Gare"}).status_code,201)
        user=User.objects.get(phone="+22370000001")
        r=self.post("company/profile",{"first_name":" Awa  Marie ","last_name":"Test","email":"other@example.com","status":"VERIFIED","role":"ADMIN"})
        self.assertEqual(r.status_code,200)
        self.assertEqual(r.json()["first_name"],"Awa Marie")
        user.refresh_from_db()
        self.assertEqual(user.email,self.payload["email"])
        self.assertEqual(Company.objects.get(owner=user).status,"PENDING")
        self.assertEqual(self.client.get("/api/v1/auth/company/").json()["address"],"Gare")
        new="Nouveau!Fleuve2026"
        values={"current_password":self.payload["password"],"password":new,"password_confirmation":new}
        self.assertEqual(self.post("company/password",{**values,"current_password":"incorrect"}).status_code,400)
        self.assertEqual(self.post("company/password",values).status_code,200)
        self.assertEqual(self.client.get("/api/v1/auth/me/").status_code,200)
        user.refresh_from_db()
        self.assertTrue(user.check_password(new))

    def test_company_profile_rejects_traveler(self):
        self.post("register/traveler",self.payload)
        self.assertEqual(self.post("company/profile",{"first_name":"A","last_name":"B"}).status_code,403)
        self.assertEqual(self.post("company/password",{}).status_code,403)
