from datetime import timedelta
from uuid import uuid4
from django.test import TestCase
from django.utils import timezone
from .models import Booking, BookingLeg, SandboxCheckout
from .test_booking import BookingFixture

class BookingHistoryTests(BookingFixture,TestCase):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.user)
        self.url="/api/v1/travel/bookings/"
    def make(self,name="Awa Traoré",status="HELD",user=None,expired=False):
        b=Booking.objects.create(traveler=user or self.user,request_id=uuid4(),passengers=1,passenger_names=[name],status=status,expires_at=timezone.now()+timedelta(minutes=-1 if expired else 15))
        BookingLeg.objects.create(booking=b,departure=self.departure,position=0,unit_price=8000)
        return b
    def test_pagination_and_private_history(self):
        old=self.make("Ancien Voyageur")
        for _ in range(20):self.make()
        self.make("Ancien Voyageur",user=self.other)
        first=self.client.get(self.url).json()
        self.assertEqual((first["total"],len(first["items"]),first["page_size"],first["has_next"]),(21,10,10,True))
        last=self.client.get(self.url,{"page":3}).json()
        self.assertEqual([r["id"] for r in last["items"]],[old.id])
        self.assertEqual(self.client.get(self.url,{"q":"ancien voyageur"}).json()["total"],1)
    def test_partial_accent_multiword_reference_date_and_amount(self):
        b=self.make("Aïssata Traoré")
        for q in ("aiss TRAORE","sika bamako","transport aissata",str(b.request_id)[:12],self.start.strftime("%d/%m/%Y"),"8 000 FCFA"):
            r=self.client.get(self.url,{"q":q})
            self.assertEqual(r.status_code,200,r.content)
            self.assertEqual(r.json()["total"],1,q)
        self.assertEqual(self.client.get(self.url,{"q":"introuvable"}).json()["total"],0)
    def test_checkout_and_expiration_filters(self):
        expired=self.make(expired=True)
        pending=self.make(expired=True)
        paid=self.make(expired=True)
        SandboxCheckout.objects.create(booking=pending,amount=8000,status="PENDING")
        SandboxCheckout.objects.create(booking=paid,amount=8000,status="PAID")
        for status,b in (("EXPIRED",expired),("SASPAY_PENDING",pending),("SASPAY_PAID",paid)):
            self.assertEqual([r["id"] for r in self.client.get(self.url,{"status":status}).json()["items"]],[b.id])
        self.assertEqual(self.client.get(self.url,{"q":"saspay confirme"}).json()["total"],1)
    def test_reject_invalid_parameters(self):
        for params in ({"page":0},{"status":"INVALID"},{"page_size":999},{"q":"x"*151}):
            self.assertEqual(self.client.get(self.url,params).status_code,400)
