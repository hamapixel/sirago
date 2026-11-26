from django.test import TestCase, Client
from .models import User, Company, CompanyCommission, CommissionChange

class CommissionTests(TestCase):
    def setUp(self):
        self.admin=User.objects.create_superuser(username="admin-commission",password="Test-pass-123")
        self.owner=User.objects.create_user(username="owner-commission",role=User.Role.COMPANY)
        self.company=Company.objects.create(owner=self.owner,name="Diarra Transport",city="Bamako",address="Gare")
        self.base="/api/v1/auth/supervision/commissions/"
        self.url=f"{self.base}{self.company.pk}/"
    def post(self,rate,expected=None):
        return self.client.post(self.url,{"rate_bps":rate,"expected_bps":expected},content_type="application/json")
    def test_permissions(self):
        self.assertEqual(self.client.get(self.base).status_code,401)
        self.assertEqual(self.post(500).status_code,401)
        self.client.force_login(self.owner)
        for path in (self.base,self.base+"history/"):
            self.assertEqual(self.client.get(path).status_code,403)
        self.assertEqual(self.post(500).status_code,403)
        self.owner.is_staff=True;self.owner.save(update_fields=["is_staff"])
        self.assertEqual(self.post(500).status_code,403)
        self.assertFalse(CompanyCommission.objects.exists())
    def test_configuration_and_audit(self):
        self.client.force_login(self.admin)
        r=self.client.get(self.base,{"q":"Diarra Bamako"}).json()
        self.assertIsNone(r["items"][0]["rate_bps"])
        self.assertEqual(self.post(500).status_code,200)
        self.assertEqual(self.post(750,500).status_code,200)
        self.assertEqual(self.post(750,750).status_code,200)
        self.assertEqual(CompanyCommission.objects.get().rate_bps,750)
        self.assertEqual(CommissionChange.objects.count(),2)
        h=self.client.get(self.base+"history/").json()
        self.assertEqual(h["items"][0]["previous_bps"],500)
        self.assertEqual(h["items"][0]["new_bps"],750)
        self.assertEqual(h["items"][0]["actor"],self.admin.username)
        self.assertEqual(self.post(0,750).status_code,200)
    def test_reject_invalid_and_stale(self):
        self.client.force_login(self.admin)
        for rate in (True,-1,1001,2.5,"500",None):
            self.assertEqual(self.post(rate).status_code,400)
        self.assertEqual(self.post(500).status_code,200)
        self.assertEqual(self.post(600).status_code,409)
        self.assertEqual(CompanyCommission.objects.get().rate_bps,500)
        self.assertEqual(CommissionChange.objects.count(),1)
    def test_csrf_required(self):
        c=Client(enforce_csrf_checks=True)
        c.force_login(self.admin)
        values={"rate_bps":500,"expected_bps":None}
        self.assertEqual(c.post(self.url,values,content_type="application/json").status_code,403)
        token=c.get("/api/v1/auth/csrf/").json()["csrfToken"]
        self.assertEqual(c.post(self.url,values,content_type="application/json",HTTP_X_CSRFTOKEN=token).status_code,200)
    def test_pagination(self):
        self.client.force_login(self.admin)
        for n in range(12):
            u=User.objects.create_user(username=f"commission-owner-{n}")
            Company.objects.create(owner=u,name=f"Transport {n}",city="Sikasso",address="Gare")
        first=self.client.get(self.base).json()
        self.assertEqual((first["total"],len(first["items"]),first["page_size"]),(13,10,10))
        self.assertEqual(len(self.client.get(self.base,{"page":2}).json()["items"]),3)
        self.assertEqual(self.client.get(self.base,{"q":"Sikasso"}).json()["total"],12)
