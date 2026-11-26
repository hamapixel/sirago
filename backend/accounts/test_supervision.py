from django.test import TestCase
from .models import User,Company,SupportRequest
from uuid import uuid4

class SupervisionTests(TestCase):
    def setUp(self):
        self.admin=User.objects.create_superuser(username="supervisor",password="Test-password-123")
        self.traveler=User.objects.create_user(username="voyageur",first_name="Awa",last_name="Test")
        self.owner=User.objects.create_user(username="owner",role=User.Role.COMPANY)
        self.company=Company.objects.create(owner=self.owner,name="Transport Test",city="Bamako",address="Gare")
        self.support=SupportRequest.objects.create(requester=self.traveler,reference=uuid4(),category="BOOKING",subject="Billet absent",message="Je ne trouve pas mon billet.")
        self.url="/api/v1/auth/supervision/"
    def test_only_superusers(self):
        for path in ("","companies/","travelers/","support/"):
            self.client.logout()
            self.assertEqual(self.client.get(self.url+path).status_code,401)
            for user in (self.traveler,self.owner):
                self.client.force_login(user)
                self.assertEqual(self.client.get(self.url+path).status_code,403)
        self.traveler.is_staff=True;self.traveler.save(update_fields=["is_staff"])
        self.client.force_login(self.traveler)
        self.assertEqual(self.client.get(self.url).status_code,403)
    def test_overview_and_read_only(self):
        self.client.force_login(self.admin)
        r=self.client.get(self.url)
        self.assertEqual(r.status_code,200,r.content)
        s=r.json()
        self.assertEqual((s["companies"],s["pending_companies"],s["travelers"],s["open_support"]),(1,1,1,1))
        self.assertFalse(s["real_payments_enabled"])
        self.assertEqual(s["real_amount"],0)
        self.assertEqual(self.client.post(self.url+"companies/").status_code,405)
    def test_lists_filters_and_minimal_fields(self):
        self.client.force_login(self.admin)
        c=self.client.get(self.url+"companies/",{"q":"Transport Bamako","status":"PENDING"}).json()
        self.assertEqual(c["total"],1)
        self.assertEqual(c["items"][0]["id"],self.company.pk)
        self.assertEqual(self.client.get(self.url+"companies/",{"status":"VERIFIED"}).json()["total"],0)
        t=self.client.get(self.url+"travelers/",{"q":"Awa Test"}).json()
        self.assertEqual(t["total"],1)
        self.assertNotIn("password",t["items"][0])
        self.assertNotIn("phone",t["items"][0])
        self.assertEqual(self.client.get(self.url+"support/",{"q":"Billet","status":"OPEN"}).json()["items"][0]["id"],self.support.pk)
        self.assertEqual(self.client.get(self.url+"support/",{"page":0}).status_code,400)
