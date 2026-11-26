from uuid import uuid4
from django.test import TestCase,Client
from django.contrib import admin
from django.test import RequestFactory
from .models import User,SupportRequest,Notification
from .admin import SupportRequestAdmin

class SupportTests(TestCase):
    def setUp(self):
        self.user=User.objects.create_user(username="traveler")
        self.other=User.objects.create_user(username="company",role="COMPANY")
        self.client.force_login(self.user)
        self.url="/api/v1/auth/support/"
        self.payload={"request_id":str(uuid4()),"category":"BOOKING","subject":"Billet absent","message":"Je ne trouve pas mon billet."}
    def post(self,**kw):
        return self.client.post(self.url,{**self.payload,**kw},content_type="application/json")
    def test_creation_retry_and_privacy(self):
        r=self.post()
        self.assertEqual(r.status_code,201,r.content)
        self.assertEqual(self.post().status_code,200)
        self.assertEqual(self.post(subject="Autre sujet").status_code,409)
        self.assertEqual(self.client.get(self.url,{"q":r.json()["reference"]}).json()["total"],1)
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(self.url).json()["total"],0)
        self.assertEqual(self.post().status_code,409)
        self.assertEqual(self.post(request_id=str(uuid4())).status_code,201)
    def test_validation_and_rate_limit(self):
        self.assertEqual(self.post(category="BAD").status_code,400)
        self.assertEqual(self.post(message="court").status_code,400)
        for _ in range(5):self.assertEqual(self.post(request_id=str(uuid4())).status_code,201)
        self.assertEqual(self.post(request_id=str(uuid4())).status_code,429)
    def test_auth_and_csrf(self):
        c=Client(enforce_csrf_checks=True);c.force_login(self.user)
        self.assertEqual(c.post(self.url,self.payload,content_type="application/json").status_code,403)
        self.client.logout()
        self.assertEqual(self.client.get(self.url).status_code,401)
    def test_admin_response_and_notification(self):
        self.assertEqual(self.post().status_code,201)
        t=SupportRequest.objects.get()
        model_admin=SupportRequestAdmin(SupportRequest,admin.site)
        request=RequestFactory().get("/admin/")
        request.user=self.other
        self.assertFalse(model_admin.has_view_permission(request))
        request.user=User.objects.create_superuser(username="admin",password="Test-password-123")
        self.assertTrue(model_admin.has_change_permission(request))
        t.reply="Votre billet est disponible.";t.status="RESOLVED"
        from types import SimpleNamespace
        model_admin.save_model(request,t,SimpleNamespace(changed_data=["reply","status"]),True)
        self.assertEqual(self.client.get(self.url).json()["items"][0]["reply"],t.reply)
        self.assertEqual(Notification.objects.filter(recipient=self.user,kind="SUPPORT").count(),1)
