"""Dedicated process; no HTTP requests from Gunicorn or booking transactions."""
import json
import os
import time
from datetime import timedelta
from django.contrib.auth import SESSION_KEY, HASH_SESSION_KEY
from django.contrib.sessions.backends.db import SessionStore
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction, close_old_connections
from django.utils import timezone
from django.utils.crypto import constant_time_compare
from requests import Session
from pywebpush import webpush, WebPushException
from accounts.models import PushDelivery, PushSubscription, CompanyAgent, Company
from accounts.push import public_key, validate_endpoint

class NoRedirect(Session):
    def request(self, method, url, **kwargs):
        validate_endpoint(url)
        kwargs["allow_redirects"]=False
        return super().request(method,url,**kwargs)

def valid_subscription(sub):
    user=sub.recipient
    if not user.is_active:return False
    values=SessionStore(session_key=sub.session_key).load()
    if str(values.get(SESSION_KEY))!=str(user.pk) or not constant_time_compare(values.get(HASH_SESSION_KEY,""),user.get_session_auth_hash()):
        return False
    return not CompanyAgent.objects.filter(user=user).exclude(company__status=Company.Status.VERIFIED).exists()

def deliver_one(session, private_key, subject):
    now=timezone.now()
    with transaction.atomic():
        delivery=PushDelivery.objects.select_for_update(skip_locked=True).filter(next_attempt__lte=now).order_by("next_attempt","pk").first()
        if not delivery:return False
        sub=PushSubscription.objects.select_related("recipient").filter(pk=delivery.subscription_id).first()
        if not sub:return True
        notice=delivery.notification
        if notice.read_at or notice.recipient_id!=sub.recipient_id or notice.created_at<now-timedelta(hours=1):
            delivery.delete()
            return True
        if not valid_subscription(sub):
            sub.delete()
            return True
        user=sub.recipient
        path="/superadmin/" if user.is_superuser else "/company/" if user.role=="COMPANY" else "/app/"
        try:
            validate_endpoint(sub.endpoint)
            webpush(subscription_info={"endpoint":sub.endpoint,"keys":{"p256dh":sub.p256dh,"auth":sub.auth}},
                data=json.dumps({"path":path,"id":notice.pk}),
                vapid_private_key=private_key,vapid_claims={"sub":subject},
                ttl=300,timeout=5,requests_session=session,headers={"Urgency":"normal"})
        except Exception as exc:
            status=exc.response.status_code if isinstance(exc,WebPushException) and exc.response is not None else None
            if status in (404,410):
                sub.delete()
            elif delivery.attempts>=2 or status in (400,401,403):
                delivery.delete()
            else:
                delivery.attempts+=1
                delivery.next_attempt=now+timedelta(seconds=60*delivery.attempts)
                delivery.save(update_fields=["attempts","next_attempt"])
            # Never log endpoint, keys, provider response or passenger data.
        else:
            delivery.delete()
        return True

class Command(BaseCommand):
    help="Deliver pending Web Push alerts using a dedicated worker."
    def handle(self,*args,**options):
        if os.environ.get("SIRAGO_PUSH_ENABLED")!="1":
            self.stdout.write("Web Push disabled.")
            return
        key=os.environ.get("SIRAGO_VAPID_PRIVATE_KEY","")
        subject=os.environ.get("SIRAGO_VAPID_SUBJECT","")
        if not public_key() or not key or not subject.startswith("mailto:"):
            raise CommandError("Missing Web Push configuration.")
        from py_vapid import Vapid
        try:
            vapid=Vapid.from_string(key)
            from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
            from accounts.push import decode_key
            if vapid.public_key.public_bytes(Encoding.X962, PublicFormat.UncompressedPoint)!=decode_key(public_key(),65):
                raise ValueError()
        except Exception:
            raise CommandError("Invalid or mismatched VAPID keys.") from None
        with NoRedirect() as session:
            session.trust_env=False
            while True:
                close_old_connections()
                if not deliver_one(session,vapid,subject):time.sleep(3)
