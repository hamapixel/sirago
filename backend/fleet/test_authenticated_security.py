"""Authenticated negative tests on Django's disposable PostgreSQL test database."""
import secrets
from datetime import timedelta
from uuid import uuid4

from django.core.cache import cache
from django.test import Client, TestCase, override_settings
from accounts.models import Company, CompanyAgent, Notification, SupportRequest, User
from .models import Booking, Bus, Departure, Route
from .test_booking import BookingFixture

AUTH = "/api/v1/auth/"
FLEET = "/api/v1/company/"
TRAVEL = "/api/v1/travel/"
XSS = '<img src=x onerror="void(0)">'
SQL_INPUTS = ("' OR '1'='1", "%' OR 1=1 --", "x'; SELECT 1; --", "%_")
 
@override_settings(SIRAGO_ADMIN_MFA_REQUIRED=True)
class AuthenticatedSecurityTests(BookingFixture, TestCase):
    def setUp(self):
        super().setUp()
        cache.clear()
        self.addCleanup(cache.clear)
        self.password = secrets.token_urlsafe(24)
        self.other_owner = User.objects.create_user(username="security-owner-b", role=User.Role.COMPANY)
        self.other_company = Company.objects.create(owner=self.other_owner, name="Private Company B",
            city="Bamako", address="Gare B", status=Company.Status.VERIFIED)
        self.other_bus = Bus.objects.create(company=self.other_company, name="Private Bus B",
            plate="SEC B01", capacity=4)
        self.other_route = Route.objects.create(company=self.other_company, origin="Bamako",
            destination="Sikasso", boarding_point="Gare B", arrival_point="Gare C",
            duration_minutes=420, price=9000)
        self.other_dep = Departure.objects.create(company=self.other_company, bus=self.other_bus,
            route=self.other_route, starts_at=self.start+timedelta(hours=1),
            ends_at=self.start+timedelta(hours=8), capacity=4, price=9000, status="PUBLISHED")
        self.clerk = User.objects.create_user(username="security-clerk", role=User.Role.COMPANY)
        self.controller = User.objects.create_user(username="security-controller", role=User.Role.COMPANY)
        self.clerk_membership = CompanyAgent.objects.create(user=self.clerk, company=self.company, role="CLERK")
        self.controller_membership = CompanyAgent.objects.create(user=self.controller, company=self.other_company, role="CONTROLLER")
        self.accounts = (self.owner, self.other_owner, self.user, self.other, self.clerk, self.controller)
        for i, user in enumerate(self.accounts):
            user.email = f"security-{i}@example.test"
            user.set_password(self.password)
            user.save(update_fields=["email", "password"])

    def csrf(self, client):
        result = client.get(AUTH+"csrf/")
        self.assertEqual(result.status_code, 200)
        return result.json()["csrfToken"]

    def post(self, client, path, payload, **headers):
        return client.post(path, payload, content_type="application/json",
                           HTTP_X_CSRFTOKEN=self.csrf(client), **headers)

    def authenticate(self, user):
        client = Client(enforce_csrf_checks=True)
        result = self.post(client, AUTH+"login/", {"identifier":user.email, "password":self.password})
        self.assertEqual(result.status_code, 200, result.content)
        self.assertEqual(result.json()["email"], user.email)
        self.assertNotIn("mfa_required", result.json())
        return client

    def book(self, client, **overrides):
        result = self.post(client, TRAVEL+"bookings/reserve/", {**self.payload, **overrides})
        self.assertEqual(result.status_code, 201, result.content)
        return Booking.objects.get(pk=result.json()["id"])

    def test_sql_input_does_not_escape_authenticated_company_search(self):
        a = self.authenticate(self.owner)
        b = self.authenticate(self.other_owner)
        self.assertEqual(a.get(FLEET+"departures/").json()["total"], 1)
        self.assertEqual(b.get(FLEET+"departures/").json()["total"], 1)
        for payload in SQL_INPUTS:
            for client in (a,b):
                for endpoint in ("departures/", "reservations/"):
                    with self.subTest(payload=payload, endpoint=endpoint):
                        response = client.get(FLEET+endpoint, {"q":payload})
                        self.assertEqual(response.status_code, 200, response.content)
                        self.assertEqual(response.json()["items"], [])
        self.assertEqual(Departure.objects.count(), 2)

    def test_sql_input_in_login_does_not_authenticate(self):
        client = Client(enforce_csrf_checks=True)
        for payload in SQL_INPUTS:
            result = self.post(client, AUTH+"login/", {"identifier":payload,"password":self.password})
            self.assertEqual(result.status_code, 401)
            self.assertNotIn("_auth_user_id", client.session)
        self.assertEqual(client.get(AUTH+"me/").status_code, 401)

    def test_other_company_read_and_write_ids_remain_private(self):
        a = self.authenticate(self.owner)
        b = self.authenticate(self.other_owner)
        self.assertEqual([v["id"] for v in b.get(FLEET+"buses/").json()["items"]], [self.other_bus.pk])
        self.assertEqual([v["id"] for v in a.get(FLEET+"buses/").json()["items"]], [self.departure.bus_id])
        for path in (
            f"buses/{self.other_bus.pk}/", f"routes/{self.other_route.pk}/",
            f"departures/{self.other_dep.pk}/", f"departures/{self.other_dep.pk}/status/",
        ):
            self.assertEqual(self.post(a,FLEET+path,{"status":"CANCELLED"}).status_code,404)
        self.assertEqual(a.get(FLEET+f"departures/{self.other_dep.pk}/manifest/").status_code,404)
        self.assertEqual(a.get(FLEET+f"departures/{self.other_dep.pk}/manifest/pdf/").status_code,404)
        self.other_dep.refresh_from_db()
        self.other_bus.refresh_from_db()
        self.other_route.refresh_from_db()
        self.assertEqual(self.other_dep.status,"PUBLISHED")
        self.assertEqual(self.other_bus.name,"Private Bus B")
        self.assertEqual(self.other_route.price,9000)

    def test_agent_cannot_elevate_role_or_manage_another_company(self):
        a = self.authenticate(self.owner)
        clerk = self.authenticate(self.clerk)
        controller = self.authenticate(self.controller)
        self.assertEqual(self.post(a,AUTH+f"company/agents/{self.controller_membership.pk}/",
                                  {"action":"disable"}).status_code,404)
        self.assertEqual(self.post(clerk,AUTH+f"company/agents/{self.clerk_membership.pk}/",
                                  {"action":"role","role":"CONTROLLER"}).status_code,403)
        self.assertEqual(self.post(controller,FLEET+f"departures/{self.other_dep.pk}/status/",
                                  {"status":"CANCELLED"}).status_code,403)
        self.assertEqual(controller.get(FLEET+"finance/").status_code,403)
        self.clerk_membership.refresh_from_db()
        self.controller.refresh_from_db()
        self.assertEqual(self.clerk_membership.role,"CLERK")
        self.assertTrue(self.controller.is_active)

    def test_traveler_booking_ids_do_not_leak_across_sessions(self):
        a = self.authenticate(self.user)
        b = self.authenticate(self.other)
        booking = self.book(a)
        base = TRAVEL+f"bookings/{booking.pk}/"
        self.assertEqual(a.get(base).status_code,200)
        self.assertEqual(b.get(base).status_code,404)
        self.assertEqual(b.get(base+"tickets/").status_code,404)
        self.assertEqual(self.post(b,base+"cancel/",{}).status_code,404)
        self.assertEqual(b.get(TRAVEL+"bookings/").json()["items"],[])
        booking.refresh_from_db()
        self.assertEqual(booking.status,Booking.Status.HELD)

    def test_reservation_details_and_finances_are_scoped(self):
        booking = self.book(self.authenticate(self.user))
        leg = booking.legs.get()
        path = FLEET+f"reservations/{leg.pk}/"
        owner = self.authenticate(self.owner)
        foreign = self.authenticate(self.other_owner)
        clerk = self.authenticate(self.clerk)
        self.assertEqual(owner.get(path).json()["total"],16000)
        self.assertEqual(foreign.get(path).status_code,404)
        self.assertEqual(foreign.get(FLEET+"reservations/").json()["items"],[])
        response = clerk.get(path)
        self.assertEqual(response.status_code,200)
        for key in ("total","real_amount","simulated_amount"):
            self.assertNotIn(key,response.json())
        for passenger in response.json()["passengers"]:
            self.assertNotIn("amount",passenger)
        self.assertIn("no-store",response["Cache-Control"])

    def test_authenticated_csrf_blocks_cross_origin_and_missing_token(self):
        owner = self.authenticate(self.owner)
        url = FLEET+f"departures/{self.departure.pk}/status/"
        payload = {"status":"SUSPENDED"}
        self.assertEqual(owner.post(url,payload,content_type="application/json").status_code,403)
        self.assertEqual(self.post(owner,url,payload,HTTP_ORIGIN="https://foreign.example.test").status_code,403)
        self.departure.refresh_from_db()
        self.assertEqual(self.departure.status,"PUBLISHED")
        self.assertEqual(self.post(owner,url,payload).status_code,200)

    def test_mass_assignment_cannot_grant_admin_or_change_owner(self):
        owner = self.authenticate(self.owner)
        response = self.post(owner,AUTH+"company/profile/",{"first_name":"Test","last_name":"Owner",
            "is_superuser":True,"is_staff":True,"role":"ADMIN","company_id":self.other_company.pk})
        self.assertEqual(response.status_code,200)
        self.owner.refresh_from_db()
        self.assertFalse(self.owner.is_superuser)
        self.assertFalse(self.owner.is_staff)
        self.assertEqual(self.owner.role,User.Role.COMPANY)
        self.other_company.refresh_from_db()
        self.assertEqual(self.other_company.owner_id,self.other_owner.pk)
        self.assertEqual(owner.get(AUTH+"supervision/").status_code,403)

    def test_stored_markup_remains_json_data_and_is_private(self):
        a = self.authenticate(self.user)
        b = self.authenticate(self.other)
        ticket = self.post(a,AUTH+"support/",{"request_id":str(uuid4()),"category":"BOOKING",
            "subject":"Security fixture", "message":XSS, "reply":"not authorized", "status":"RESOLVED"})
        self.assertEqual(ticket.status_code,201,ticket.content)
        response = a.get(AUTH+"support/")
        self.assertTrue(response["Content-Type"].startswith("application/json"))
        self.assertIn("no-store",response["Cache-Control"])
        self.assertEqual(response.json()["items"][0]["message"],XSS)
        self.assertEqual(response.json()["items"][0]["reply"],"")
        self.assertNotEqual(response.json()["items"][0]["status"],"RESOLVED")
        self.assertEqual(b.get(AUTH+"support/").json()["items"],[])
        booking = self.book(a,passenger_names=[XSS,"Moussa Test"])
        result = self.authenticate(self.owner).get(FLEET+f"reservations/{booking.legs.get().pk}/")
        self.assertEqual(result.status_code,200)
        self.assertEqual(result.json()["passengers"][0]["name"],XSS)

    def test_notification_id_cannot_be_mutated_by_another_user(self):
        a = self.authenticate(self.user)
        b = self.authenticate(self.other)
        notice = Notification.objects.create(recipient=self.user,kind="DEPARTURE",title="Private",message="Test")
        self.assertEqual(self.post(b,AUTH+f"notifications/{notice.pk}/read/",{}).status_code,404)
        notice.refresh_from_db()
        self.assertIsNone(notice.read_at)
        self.assertEqual(self.post(a,AUTH+f"notifications/{notice.pk}/read/",{}).status_code,200)
        notice.refresh_from_db()
        self.assertIsNotNone(notice.read_at)

    def test_logout_revokes_session_and_privileged_apis(self):
        a = self.authenticate(self.owner)
        cookie = a.cookies["sessionid"].value
        self.assertEqual(self.post(a,AUTH+"logout/",{}).status_code,200)
        replay = Client(enforce_csrf_checks=True)
        replay.cookies["sessionid"] = cookie
        self.assertEqual(replay.get(FLEET+"dashboard/").status_code,401)
        self.assertEqual(replay.get(AUTH+"me/").status_code,401)
