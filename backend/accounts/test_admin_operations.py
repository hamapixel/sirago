from uuid import uuid4
from datetime import timedelta
from django.test import TestCase, Client, override_settings
from django.utils import timezone
from .models import User, Company, SupportRequest, AdminMFA, AdminAction, Notification
from .mfa import VERIFIED
from fleet.models import Bus, Route, Departure, Booking, BookingLeg

@override_settings(SIRAGO_ADMIN_MFA_REQUIRED=True)
class AdminOperationsTests(TestCase):
    def setUp(self):
        self.admin=User.objects.create_superuser(username="ops-admin")
        self.traveler=User.objects.create_user(username="ops-traveler",password="Local-example-123")
        self.owner=User.objects.create_user(username="ops-owner",role=User.Role.COMPANY)
        self.company=Company.objects.create(owner=self.owner,name="Transport",city="Bamako",address="Gare")
        self.ticket=SupportRequest.objects.create(requester=self.traveler,reference=uuid4(),
            category="BOOKING",subject="Billet",message="<script>test</script>")
        self.state=AdminMFA.objects.create(user=self.admin,enabled=True)
        self.base="/api/v1/auth/supervision/"
        self.client.force_login(self.admin)
        session=self.client.session
        session[VERIFIED]=str(self.state.version)
        session.save()

    def post(self,path,**values):
        return self.client.post(self.base+path,{"confirm":True,"reason":"Recette administrative",**values},content_type="application/json")

    def test_mfa_csrf_and_roles(self):
        path=f"companies/{self.company.pk}/"
        for u,expected in ((self.traveler,403),(self.owner,403),(self.admin,401)):
            c=Client()
            c.force_login(u)
            self.assertEqual(c.get(self.base+path).status_code,expected)
        self.assertEqual(Client().get(self.base+path).status_code,401)
        c=Client(enforce_csrf_checks=True)
        c.force_login(self.admin)
        session=c.session
        session[VERIFIED]=str(self.state.version)
        session.save()
        self.assertEqual(c.post(self.base+path,{"confirm":True},content_type="application/json").status_code,403)
        self.assertEqual(AdminAction.objects.count(),0)

    def test_company_transitions_and_stale_or_extra_fields(self):
        path=f"companies/{self.company.pk}/"
        self.assertEqual(self.post(path,status="VERIFIED",expected_status="PENDING",owner=42).status_code,400)
        self.assertEqual(self.post(path,status="VERIFIED",expected_status="PENDING",confirm=False).status_code,400)
        self.assertEqual(self.post(path,status="VERIFIED",expected_status="PENDING").status_code,200)
        self.assertEqual(self.post(path,status="SUSPENDED",expected_status="PENDING").status_code,409)
        self.assertEqual(self.post(path,status="SUSPENDED",expected_status="VERIFIED").status_code,200)
        self.assertEqual(self.post(path,status="VERIFIED",expected_status="SUSPENDED").status_code,200)
        self.assertEqual(AdminAction.objects.filter(target_type="COMPANY").count(),3)
        self.assertEqual(Notification.objects.filter(recipient=self.owner).count(),3)
        response=self.client.get(self.base+"actions/")
        self.assertEqual(response.json()["total"],3)
        self.assertIn("no-store",response["Cache-Control"])
        self.assertEqual(self.client.post(self.base+"actions/").status_code,405)

    def test_traveler_revocation_and_reactivation_preserve_password(self):
        c=Client()
        c.force_login(self.traveler)
        saved=self.traveler.password
        path=f"travelers/{self.traveler.pk}/"
        self.assertEqual(self.post(path,active=False,expected_active=True).status_code,200)
        self.assertEqual(self.post(path,active=True,expected_active=False).status_code,200)
        self.assertEqual(c.get("/api/v1/auth/me/").status_code,401)
        self.traveler.refresh_from_db()
        self.assertEqual(self.traveler.password,saved)
        self.assertTrue(self.traveler.is_active)
        self.assertEqual(self.post(f"travelers/{self.admin.pk}/",active=False,expected_active=True).status_code,404)
        self.assertEqual(self.post(f"travelers/{self.owner.pk}/",active=False,expected_active=True).status_code,404)
        self.assertEqual(AdminAction.objects.count(),2)

    def test_support_reply_and_stale_version(self):
        path=f"support/{self.ticket.pk}/"
        d=self.client.get(self.base+path).json()
        self.assertEqual(d["message"],self.ticket.message)
        self.assertEqual(self.post(path,status="RESOLVED",reply="",expected_updated_at=d["updated_at"]).status_code,400)
        self.assertEqual(self.post(path,status="RESOLVED",reply="Votre billet est disponible.",expected_updated_at=d["updated_at"]).status_code,200)
        self.assertEqual(self.post(path,status="OPEN",reply="Autre",expected_updated_at=d["updated_at"]).status_code,409)
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.status,"RESOLVED")
        self.assertEqual(AdminAction.objects.count(),1)
        self.assertEqual(Notification.objects.filter(recipient=self.traveler,kind="SUPPORT").count(),1)

    def test_future_booking_prevents_suspension_or_deactivation(self):
        self.company.status="VERIFIED";self.company.save(update_fields=["status"])
        bus=Bus.objects.create(company=self.company,name="Car",plate="TEST 10",capacity=10)
        route=Route.objects.create(company=self.company,origin="Bamako",destination="Sikasso",boarding_point="Gare",arrival_point="Gare B",duration_minutes=60,price=8000)
        start=timezone.now()+timedelta(days=1)
        d=Departure.objects.create(company=self.company,bus=bus,route=route,starts_at=start,ends_at=start+timedelta(hours=1),capacity=10,price=8000,status="PUBLISHED")
        booking=Booking.objects.create(traveler=self.traveler,request_id=uuid4(),passengers=1,expires_at=timezone.now()+timedelta(minutes=10))
        BookingLeg.objects.create(booking=booking,departure=d,position=0,unit_price=8000)
        self.assertEqual(self.post(f"companies/{self.company.pk}/",status="SUSPENDED",expected_status="VERIFIED").status_code,409)
        self.assertEqual(self.post(f"travelers/{self.traveler.pk}/",active=False,expected_active=True).status_code,409)
        self.assertEqual(AdminAction.objects.count(),0)
