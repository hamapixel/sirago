from datetime import timedelta
from django.test import TestCase, override_settings
from django.utils import timezone
from accounts.models import Company, CompanyAgent, User
from .models import Booking, BookingLeg, Departure, Bus, Route
from .test_booking import BookingFixture

@override_settings(DEBUG=True,SIRAGO_ENABLE_SIMULATED_PAYMENTS=True)
class ReservationDetailTests(BookingFixture,TestCase):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.user)
        r=self.reserve()
        self.assertEqual(r.status_code,201,r.content)
        self.booking=Booking.objects.get(pk=r.json()["id"])
        self.leg=self.booking.legs.get()
        self.base=f"/api/v1/travel/bookings/{self.booking.pk}/"
        self.detail=f"/api/v1/company/reservations/{self.leg.pk}/"

    def test_owner_names_prices_and_boarding(self):
        self.client.force_login(self.owner)
        r=self.client.get(self.detail)
        self.assertEqual(r.status_code,200,r.content)
        self.assertIn("no-store",r["Cache-Control"])
        d=r.json()
        self.assertEqual([p["name"] for p in d["passengers"]],["Awa Test","Moussa Test"])
        self.assertEqual(d["total"],16000)
        self.assertEqual(d["real_amount"],0)
        self.assertEqual(d["simulated_amount"],0)
        self.assertEqual([p["state"] for p in d["passengers"]],["PENDING","PENDING"])
        self.assertEqual(d["boarding_point"],"Gare A")
        self.client.force_login(self.user)
        self.assertEqual(self.client.post(self.base+"simulate-payment/",{"network":"orange_ml"},content_type="application/json").status_code,200)
        code=self.client.get(self.base+"tickets/").json()["items"][0]["code"]
        self.client.force_login(self.owner)
        self.assertEqual(self.client.post("/api/v1/company/boarding/validate/",{"code":code,"passengers":[0]},content_type="application/json").status_code,200)
        d=self.client.get(self.detail).json()
        self.assertEqual(d["boarded_count"],1)
        self.assertEqual([p["state"] for p in d["passengers"]],["BOARDED","WAITING"])
        self.assertIsNotNone(d["passengers"][0]["boarded_at"])
        self.assertEqual(d["simulated_amount"],16000)
        self.assertNotIn(code,str(d))
        self.assertNotIn("traveler",d)

    def test_permissions_and_agent_redaction(self):
        self.assertEqual(self.client.get(self.detail).status_code,403)
        self.client.logout()
        self.assertEqual(self.client.get(self.detail).status_code,401)
        other=User.objects.create_user(username="detail-other",role=User.Role.COMPANY)
        Company.objects.create(owner=other,name="Autre",city="Bamako",address="Gare",status="VERIFIED")
        self.client.force_login(other)
        self.assertEqual(self.client.get(self.detail).status_code,404)
        agent=User.objects.create_user(username="detail-clerk",role=User.Role.COMPANY)
        membership=CompanyAgent.objects.create(user=agent,company=self.company,role="CLERK")
        self.client.force_login(agent)
        r=self.client.get(self.detail)
        self.assertEqual(r.status_code,200,r.content)
        d=r.json()
        for key in ("total","simulated_amount","real_amount"):
            self.assertNotIn(key,d)
        self.assertNotIn("amount",d["passengers"][0])
        self.assertEqual(self.client.post(self.detail,{},content_type="application/json").status_code,403)
        membership.role="CONTROLLER";membership.save(update_fields=["role"])
        self.assertEqual(self.client.get(self.detail).status_code,403)
        self.client.force_login(self.owner)
        self.assertEqual(self.client.post(self.detail,{},content_type="application/json").status_code,405)
        self.company.status="SUSPENDED";self.company.save(update_fields=["status"])
        self.assertEqual(self.client.get(self.detail).status_code,403)

    def test_expired_booking_and_premium_category(self):
        self.leg.premium_count=1;self.leg.premium_positions=[1];self.leg.premium_unit_price=12000
        self.leg.save(update_fields=["premium_count","premium_positions","premium_unit_price"])
        Booking.objects.filter(pk=self.booking.pk).update(expires_at=timezone.now()-timedelta(seconds=1))
        self.client.force_login(self.owner)
        d=self.client.get(self.detail).json()
        self.assertEqual(d["status"],"EXPIRED")
        self.assertEqual([p["category"] for p in d["passengers"]],["Standard","Premium"])
        self.assertEqual([p["amount"] for p in d["passengers"]],[8000,12000])
        self.assertEqual([p["state"] for p in d["passengers"]],["UNAVAILABLE","UNAVAILABLE"])
        self.assertEqual(d["total"],20000)

    def test_round_trip_isolates_other_company_segment(self):
        owner=User.objects.create_user(username="return-owner",role=User.Role.COMPANY)
        company=Company.objects.create(owner=owner,name="Retour",city="Sikasso",address="Gare",status="VERIFIED")
        bus=Bus.objects.create(company=company,name="Retour 01",plate="BB 001",capacity=2)
        route=Route.objects.create(company=company,origin="Sikasso",destination="Bamako",boarding_point="Gare B",arrival_point="Gare A",duration_minutes=420,price=7000)
        dep=Departure.objects.create(company=company,bus=bus,route=route,starts_at=self.start+timedelta(days=1),ends_at=self.start+timedelta(days=1,hours=7),price=7000,capacity=2,status="PUBLISHED")
        leg=BookingLeg.objects.create(booking=self.booking,departure=dep,position=1,unit_price=7000)
        url=f"/api/v1/company/reservations/{leg.pk}/"
        self.client.force_login(self.owner)
        self.assertEqual(self.client.get(url).status_code,404)
        d=self.client.get(self.detail).json()
        self.assertEqual(d["total"],16000)
        self.assertNotIn("Retour 01",str(d))
        self.client.force_login(owner)
        self.assertEqual(self.client.get(self.detail).status_code,404)
        d=self.client.get(url).json()
        self.assertEqual((d["position"],d["total"],d["origin"]),(1,14000,"Sikasso"))
