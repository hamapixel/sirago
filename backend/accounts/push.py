"""Opt-in Web Push; only known HTTPS push providers, never arbitrary URLs."""
import base64
import os
import re
from urllib.parse import urlsplit
from django.db import transaction, IntegrityError
from django.contrib.sessions.models import Session
from django.core.cache import cache
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_GET, require_POST
from cryptography.hazmat.primitives.asymmetric import ec
from .models import PushSubscription, User
from .notifications import accessible
from .views import data, error

PROVIDERS = {
    "fcm.googleapis.com": ("/fcm/send/",),
    "updates.push.services.mozilla.com": ("/wpush/",),
    "web.push.apple.com": ("/",),
}

def validate_endpoint(value):
    if not isinstance(value,str) or len(value)>2048 or not value.isascii() or any(ord(ch)<33 for ch in value) or "\\" in value:
        raise ValueError("Adresse push invalide.")
    try:
        parts=urlsplit(value)
        allowed=PROVIDERS.get(parts.hostname)
        if (parts.scheme!="https" or not allowed or parts.netloc!=parts.hostname or
            parts.query or parts.fragment or not any(parts.path.startswith(p) and len(parts.path)>len(p) for p in allowed)
            or not re.fullmatch(r"/[A-Za-z0-9_./~:%!$&'()*+,;=@-]+",parts.path)
            or "%" in parts.path or any(p in (".","..") for p in parts.path.split("/"))):
            raise ValueError()
    except ValueError:
        raise ValueError("Fournisseur push non pris en charge.")
    return value

def decode_key(value, length):
    if not isinstance(value,str) or not re.fullmatch(r"[A-Za-z0-9_-]+",value) or len(value)>100:
        raise ValueError("Clé push invalide.")
    raw=base64.urlsafe_b64decode(value+"="*(-len(value)%4))
    if len(raw)!=length:
        raise ValueError("Clé push invalide.")
    return raw

def public_key():
    if os.environ.get("SIRAGO_PUSH_ENABLED")!="1":
        return ""
    value=os.environ.get("SIRAGO_VAPID_PUBLIC_KEY","")
    try:
        ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256R1(),decode_key(value,65))
        return value
    except (ValueError,TypeError):
        return ""

@never_cache
@require_GET
def config(request):
    _,denied=accessible(request)
    if denied is not None:return denied
    return JsonResponse({"public_key":public_key()})

@never_cache
@csrf_protect
@require_POST
def subscribe(request):
    _,denied=accessible(request)
    if denied is not None:return denied
    if not public_key():return error("Notifications externes non configurées.",503)
    rate_key=f'push:subscribe:{request.user.pk}'
    if not cache.add(rate_key,1,600):
        try:
            if cache.incr(rate_key)>20:return error('Trop de tentatives.',429)
        except ValueError:
            cache.add(rate_key,1,600)
    try:
        values=data(request)
        endpoint=validate_endpoint(values.get("endpoint"))
        keys=values.get("keys")
        if not isinstance(keys,dict):raise ValueError("Clés push invalides.")
        ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256R1(),decode_key(keys.get("p256dh"),65))
        decode_key(keys.get("auth"),16)
        session_key=request.session.session_key
        if not session_key: return error("Session indisponible.",401)
        with transaction.atomic():
            User.objects.select_for_update().get(pk=request.user.pk)
            existing=PushSubscription.objects.select_for_update().filter(endpoint=endpoint).first()
            if existing and (existing.p256dh!=keys["p256dh"] or existing.auth!=keys["auth"]):
                return error("Abonnement incompatible. Réactivez les alertes.",409)
            if existing and existing.recipient_id==request.user.pk and existing.session_key==session_key:
                return JsonResponse({"enabled":True})
            active_sessions=Session.objects.filter(expire_date__gt=timezone.now()).values('session_key')
            PushSubscription.objects.filter(recipient=request.user).exclude(session_key__in=active_sessions).delete()
            if PushSubscription.objects.filter(recipient=request.user).exclude(endpoint=endpoint).count()>=5:
                return error("Limite de cinq appareils atteinte.",409)
            if existing:existing.delete()
            PushSubscription.objects.create(recipient=request.user,session_key=session_key,endpoint=endpoint,p256dh=keys["p256dh"],auth=keys["auth"])
        return JsonResponse({"enabled":True})
    except (ValueError,TypeError):return error("Abonnement push invalide.")
    except IntegrityError:return error("Abonnement concurrent. Réessayez.",409)

@never_cache
@csrf_protect
@require_POST
def unsubscribe(request):
    _,denied=accessible(request)
    if denied is not None:return denied
    try:endpoint=validate_endpoint(data(request).get("endpoint"))
    except (ValueError,TypeError):return error("Abonnement invalide.")
    PushSubscription.objects.filter(recipient=request.user,session_key=request.session.session_key,endpoint=endpoint).delete()
    return JsonResponse({"enabled":False})

@never_cache
@csrf_protect
@require_POST
def status(request):
    _,denied=accessible(request)
    if denied is not None:return denied
    try:endpoint=validate_endpoint(data(request).get("endpoint"))
    except (ValueError,TypeError):return error("Abonnement invalide.")
    return JsonResponse({"enabled":PushSubscription.objects.filter(recipient=request.user,session_key=request.session.session_key,endpoint=endpoint).exists()})
