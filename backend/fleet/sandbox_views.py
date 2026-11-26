"""Staged local Sandbox integration. No ticket issuance or financial booking."""
import os
from datetime import timedelta
from django.db import transaction
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST
from accounts.models import User, Company
from accounts.views import error
from .models import Booking, Departure, SandboxCheckout
from .booking_views import traveler_error, booking_json
from .saspay import sandbox_enabled, create_booking_checkout, verify_booking_checkout, SasPayError

def allowed(request):
    denied=traveler_error(request)
    if denied is not None:return denied
    if not sandbox_enabled():return error("Checkout Sandbox désactivé.",404)
    return None

@never_cache
@csrf_protect
@require_POST
def create(request,pk):
    denied=allowed(request)
    if denied is not None:return denied
    if not 1<=pk<=2**63-1:return error("Réservation introuvable.",404)
    with transaction.atomic():
        User.objects.select_for_update().get(pk=request.user.pk)
        b=Booking.objects.select_for_update().filter(pk=pk,traveler=request.user).first()
        if b is None:return error("Réservation introuvable.",404)
        if hasattr(b,"sandbox_checkout"):return JsonResponse(booking_json(b))
        ids=list(b.legs.values_list("departure__company_id",flat=True).distinct())
        list(Company.objects.select_for_update().filter(pk__in=ids).order_by("pk"))
        now=timezone.now()
        legs=list(b.legs.select_related("departure__company","departure__bus","departure__route"))
        if b.status!=Booking.Status.HELD or b.expires_at<=now+timedelta(seconds=30) or not legs or any(l.departure.starts_at<=now or l.departure.status!=Departure.Status.PUBLISHED or l.departure.company.status!=Company.Status.VERIFIED or not l.departure.bus.active or not l.departure.route.active for l in legs):
            return error("Réservation ou départ indisponible.",409)
        # Durable marker commits before the remote call: ambiguous failures are never retried.
        attempt=SandboxCheckout.objects.create(booking=b,amount=sum(l.total for l in legs))
    try:
        sid,url=create_booking_checkout(os.environ.get("SASPAY_API_KEY",""),b,attempt.amount)
    except SasPayError:
        SandboxCheckout.objects.filter(pk=attempt.pk).update(status="UNKNOWN")
        return error("Création incertaine. Vérifiez le tableau SasPay ; ne recréez pas la session.",502)
    SandboxCheckout.objects.filter(pk=attempt.pk).update(provider_id=sid,checkout_url=url,status="PENDING")
    return JsonResponse(booking_json(Booking.objects.get(pk=b.pk)),status=201)

@never_cache
@csrf_protect
@require_POST
def verify(request,pk):
    denied=allowed(request)
    if denied is not None:return denied
    if not 1<=pk<=2**63-1:return error("Réservation introuvable.",404)
    with transaction.atomic():
        b=Booking.objects.select_for_update().filter(pk=pk,traveler=request.user).first()
        if b is None or not hasattr(b,"sandbox_checkout"):return error("Session introuvable.",404)
        a=b.sandbox_checkout
        if not a.provider_id:return error("Session incertaine. Consultez SasPay.",409)
        if a.status in ("PAID","LATE_PAID","EXPIRED","CANCELLED"):return JsonResponse(booking_json(b))
        now=timezone.now()
        if a.checked_at and a.checked_at>now-timedelta(seconds=5):return JsonResponse(booking_json(b))
        a.checked_at=now;a.save(update_fields=["checked_at"])
    try:
        status=verify_booking_checkout(os.environ.get("SASPAY_API_KEY",""),b,a)
    except SasPayError:
        return error("Confirmation SasPay indisponible ou non conforme.",502)
    # Avoid a stale PENDING response overwriting a terminal state.
    SandboxCheckout.objects.filter(pk=a.pk,status="PENDING").update(status=status)
    return JsonResponse(booking_json(Booking.objects.get(pk=b.pk)))
