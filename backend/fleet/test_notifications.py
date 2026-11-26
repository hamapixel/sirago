from django.test import TestCase,Client,override_settings
from accounts.models import Notification
from .test_booking import BookingFixture

@override_settings(DEBUG=True,SIRAGO_ENABLE_SIMULATED_PAYMENTS=True)
class NotificationTests(BookingFixture,TestCase):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.user)
        r=self.reserve()
        self.assertEqual(r.status_code,201,r.content)
        self.base=f'/api/v1/travel/bookings/{r.json()["id"]}/'
        self.inbox="/api/v1/auth/notifications/"

    def pay(self):
        return self.client.post(self.base+"simulate-payment/",{"network":"orange_ml"},content_type="application/json")

    def test_reservation_and_payment_no_duplicate(self):
        self.assertEqual(self.reserve().status_code,200)
        self.assertEqual(Notification.objects.filter(recipient=self.user,kind="RESERVATION").count(),1)
        self.assertEqual(self.pay().status_code,200)
        self.assertEqual(self.pay().status_code,200)
        self.assertEqual(Notification.objects.filter(recipient=self.user,kind="TEST_PAYMENT").count(),1)
        self.assertEqual(Notification.objects.filter(recipient=self.owner,kind="TEST_BOOKING").count(),1)
        self.assertEqual(self.client.get(self.inbox+"count/").json()["unread_count"],2)

    def test_private_read_and_csrf(self):
        n=Notification.objects.get(recipient=self.user)
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(self.inbox).json()["total"],0)
        self.assertEqual(self.client.post(self.inbox+f"{n.pk}/read/").status_code,404)
        self.client.force_login(self.user)
        c=Client(enforce_csrf_checks=True);c.force_login(self.user)
        self.assertEqual(c.post(self.inbox+"read-all/").status_code,403)
        self.assertEqual(self.client.post(self.inbox+f"{n.pk}/read/").json()["unread_count"],0)
        self.assertEqual(self.client.get(self.inbox,{"unread":"1"}).json()["total"],0)
        self.assertEqual(self.client.get(self.inbox,{"page":"0"}).status_code,400)
        self.assertEqual(self.client.post(self.inbox+"read-all/").status_code,200)
        self.client.logout()
        self.assertEqual(self.client.get(self.inbox).status_code,401)

    def test_departure_and_boarding_notifications(self):
        self.assertEqual(self.pay().status_code,200)
        code=self.client.get(self.base+"tickets/").json()["items"][0]["code"]
        self.client.force_login(self.owner)
        url=f"/api/v1/company/departures/{self.departure.pk}/status/"
        self.assertEqual(self.client.post(url,{"status":"SUSPENDED"},content_type="application/json").status_code,200)
        self.assertEqual(self.client.post(url,{"status":"PUBLISHED"},content_type="application/json").status_code,200)
        self.assertEqual(Notification.objects.filter(recipient=self.user,kind="DEPARTURE").count(),2)
        for _ in range(2):
            self.assertEqual(self.client.post("/api/v1/company/boarding/validate/",{"code":code,"passengers":[0]},content_type="application/json").status_code,200)
        self.assertEqual(Notification.objects.filter(recipient=self.user,kind="TEST_BOARDING").count(),1)
        self.assertEqual(Notification.objects.filter(recipient=self.owner,kind="TEST_BOARDING").count(),1)

    def test_cancel_and_pagination(self):
        self.assertEqual(self.client.post(self.base+"cancel/").status_code,200)
        self.assertEqual(self.client.post(self.base+"cancel/").status_code,200)
        self.assertEqual(Notification.objects.filter(recipient=self.user,kind="CANCELLED").count(),1)
        Notification.objects.bulk_create([Notification(recipient=self.user,kind="DEPARTURE",title="Information",message="Test") for _ in range(11)])
        first=self.client.get(self.inbox).json()
        second=self.client.get(self.inbox,{"page":2}).json()
        self.assertEqual(first["total"],13)
        self.assertEqual(len(first["items"]),10)
        self.assertEqual(len(second["items"]),3)
        self.assertFalse(set(x["id"] for x in first["items"]) & set(x["id"] for x in second["items"]))
        self.assertEqual(self.client.post(self.inbox+"read-all/").json()["unread_count"],0)
