import base64
import json
from unittest.mock import patch
from uuid import uuid4
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from django.core.cache import cache
from django.test import TestCase, Client, override_settings
from accounts.test_helpers import force_mfa_login
from accounts.models import User, Notification, PushSubscription, PushDelivery
from accounts.notifications import notify
from accounts.management.commands.send_web_push import deliver_one, valid_subscription
from accounts.push import validate_endpoint

def b64(data):
    return base64.urlsafe_b64encode(data).decode().rstrip("=")

@override_settings(SIRAGO_ADMIN_MFA_REQUIRED=True)
class PushTests(TestCase):
    def setUp(self):
        cache.clear()
        self.addCleanup(cache.clear)
        self.a=User.objects.create_user(username="push-a")
        self.b=User.objects.create_user(username="push-b")
        self.admin=User.objects.create_superuser(username="push-admin")
        key=ec.generate_private_key(ec.SECP256R1()).public_key()
        self.key=b64(key.public_bytes(Encoding.X962,PublicFormat.UncompressedPoint))
        env=patch.dict("os.environ",{"SIRAGO_PUSH_ENABLED":"1","SIRAGO_VAPID_PUBLIC_KEY":self.key})
        env.start()
        self.addCleanup(env.stop)
        self.client.force_login(self.a)
        self.base="/api/v1/auth/notifications/"
        self.payload={"endpoint":"https://fcm.googleapis.com/fcm/send/example123","keys":{"p256dh":self.key,"auth":b64(bytes(16))}}

    def post(self,path,payload):
        return self.client.post(self.base+"push/"+path+"/",payload,content_type="application/json")

    def test_admin_private_inbox_and_support_event(self):
        self.client.post("/api/v1/auth/support/",{"request_id":str(uuid4()),"category":"BOOKING","subject":"Billet absent","message":"Je ne trouve pas mon billet."},content_type="application/json")
        self.assertEqual(Notification.objects.filter(recipient=self.admin,kind="SUPPORT_NEW").count(),1)
        self.assertEqual(self.client.get(self.base).json()["total"],0)
        force_mfa_login(self.client, self.admin)
        self.assertEqual(self.client.get(self.base+"count/").json()["unread_count"],1)

    def test_opt_in_is_private_and_idempotent(self):
        self.assertEqual(self.post("subscribe",self.payload).status_code,200)
        self.assertEqual(self.post("subscribe",self.payload).status_code,200)
        self.assertEqual(PushSubscription.objects.count(),1)
        self.assertTrue(self.post("status",{"endpoint":self.payload["endpoint"]}).json()["enabled"])
        self.client.force_login(self.b)
        self.assertFalse(self.post("status",{"endpoint":self.payload["endpoint"]}).json()["enabled"])
        self.post("unsubscribe",{"endpoint":self.payload["endpoint"]})
        self.assertEqual(PushSubscription.objects.count(),1)

    def test_invalid_endpoints_and_csrf(self):
        for endpoint in ["http://fcm.googleapis.com/fcm/send/x","https://127.0.0.1/private","https://fcm.googleapis.com.evil.org/fcm/send/x","https://fcm.googleapis.com/fcm/send/../x","https://fcm.googleapis.com:443/fcm/send/x","https://fcm.googleapis.com/fcm/send/x?redirect=https://evil.org"]:
            with self.subTest(endpoint=endpoint):
                self.assertEqual(self.post("subscribe",{**self.payload,"endpoint":endpoint}).status_code,400)
        client=Client(enforce_csrf_checks=True);client.force_login(self.a)
        self.assertEqual(client.post(self.base+"push/subscribe/",self.payload,content_type="application/json").status_code,403)
        self.assertFalse(PushSubscription.objects.exists())

    def test_logout_removes_subscription_and_queue(self):
        self.post("subscribe",self.payload)
        notify(self.a.pk,"RESERVATION","Réservation","Informations personnelles")
        self.assertEqual(PushDelivery.objects.count(),1)
        self.client.post("/api/v1/auth/logout/")
        self.assertFalse(PushSubscription.objects.exists())
        self.assertFalse(PushDelivery.objects.exists())

    @patch("accounts.management.commands.send_web_push.webpush")
    def test_worker_sends_generic_payload_only_for_recipient(self,send):
        self.post("subscribe",self.payload)
        notify(self.b.pk,"RESERVATION","Réservation","Autre compte")
        n=notify(self.a.pk,"RESERVATION","Réservation","Nom privé et montant")
        self.assertEqual(PushDelivery.objects.count(),1)
        self.assertTrue(deliver_one(None,"dummy","mailto:test@example.org"))
        self.assertEqual(json.loads(send.call_args.kwargs["data"]),{"path":"/app/","id":n.pk,"kind":"RESERVATION"})
        self.assertFalse(PushDelivery.objects.exists())

    @patch("accounts.management.commands.send_web_push.webpush")
    def test_expired_session_does_not_send(self,send):
        self.post("subscribe",self.payload)
        notify(self.a.pk,"RESERVATION","Réservation","Private")
        self.client.logout()
        self.assertTrue(deliver_one(None,"dummy","mailto:test@example.org"))
        send.assert_not_called()
        self.assertFalse(PushSubscription.objects.exists())

    @patch("accounts.management.commands.send_web_push.webpush",side_effect=OSError("network"))
    def test_failure_retries_without_losing_inbox(self,send):
        self.post("subscribe",self.payload)
        notify(self.a.pk,"RESERVATION","Réservation","Private")
        self.assertTrue(deliver_one(None,"dummy","mailto:test@example.org"))
        self.assertEqual(PushDelivery.objects.get().attempts,1)
        self.assertEqual(Notification.objects.filter(recipient=self.a).count(),1)

    @patch("accounts.management.commands.send_web_push.webpush")
    def test_worker_boarding_event_is_typed_and_private(self,send):
        self.assertEqual(self.post("subscribe",self.payload).status_code,200)
        n=notify(self.a.pk,"TEST_BOARDING","Private name","Private route and amount")
        self.assertTrue(deliver_one(None,"dummy","mailto:test@example.org"))
        self.assertEqual(json.loads(send.call_args.kwargs["data"]),{"path":"/app/","id":n.pk,"kind":"TEST_BOARDING"})

    def test_inbox_read_and_ticket_filters_preserve_history_and_privacy(self):
        ticket=notify(self.a.pk,"TEST_PAYMENT","Billet test","PDF",booking_id=42)
        other=notify(self.a.pk,"RESERVATION","Réservation","Message")
        notify(self.b.pk,"TEST_PAYMENT","Autre billet","Privé",booking_id=99)
        self.assertEqual(self.client.post(self.base+f"{ticket.pk}/read/").status_code,200)
        def inbox(**params):
            response=self.client.get(self.base,params)
            self.assertEqual(response.status_code,200,response.content)
            return response.json()
        self.assertEqual(inbox()["total"],2)
        self.assertEqual(inbox()["unread_count"],1)
        self.assertEqual([n["id"] for n in inbox(read="1")["items"]],[ticket.pk])
        self.assertEqual([n["id"] for n in inbox(unread="1")["items"]],[other.pk])
        self.assertEqual(inbox(category="tickets")["items"][0]["booking_id"],42)
        self.assertEqual(inbox(category="tickets",unread="1")["total"],0)
        self.assertEqual(inbox(category="tickets",read="1")["total"],1)
        self.assertEqual(self.client.get(self.base,{"read":"1","unread":"1"}).status_code,400)
        self.assertEqual(self.client.get(self.base,{"category":"invalid"}).status_code,400)
        self.assertEqual(Notification.objects.filter(recipient=self.a).count(),2)

    def test_inbox_paginates_large_read_history(self):
        for i in range(23):
            notice=notify(self.a.pk,"TEST_PAYMENT",f"Billet {i}","PDF",booking_id=i+1)
            Notification.objects.filter(pk=notice.pk).update(read_at=notice.created_at)
        first=self.client.get(self.base,{"category":"tickets","read":"1","page":1}).json()
        last=self.client.get(self.base,{"category":"tickets","read":"1","page":3}).json()
        self.assertEqual((first["total"],len(first["items"]),first["has_next"]),(23,10,True))
        self.assertEqual((last["total"],len(last["items"]),last["has_next"]),(23,3,False))
        self.assertGreater(first["items"][-1]["id"],last["items"][0]["id"])
