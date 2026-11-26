"""Read-only platform supervision restricted to authenticated superusers."""
from functools import wraps
from django.db.models import Q, Count
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET
from fleet.models import Booking, Bus, Departure, TestBoarding
from fleet.availability import active_legs
from fleet.listing import page_slice, search_term
from .models import User, Company, CompanyAgent, SupportRequest
from .views import error

def superuser_endpoint(fn):
    @never_cache
    @require_GET
    @wraps(fn)
    def wrapped(request):
        if not request.user.is_authenticated:return error("Connexion requise.",401)
        if not request.user.is_active or not request.user.is_superuser:return error("Accès réservé au superadministrateur.",403)
        try:return fn(request)
        except (ValueError, OverflowError) as exc:return error(str(exc))
    return wrapped

@superuser_endpoint
def overview(request):
    now=timezone.now()
    counts={r["status"]:r["n"] for r in Company.objects.values("status").annotate(n=Count("id"))}
    active=active_legs(now)
    return JsonResponse({
        "companies":sum(counts.values()),"verified_companies":counts.get("VERIFIED",0),
        "pending_companies":counts.get("PENDING",0),"suspended_companies":counts.get("SUSPENDED",0),
        "travelers":User.objects.filter(role=User.Role.TRAVELER,is_superuser=False,is_active=True).count(),
        "agents":CompanyAgent.objects.filter(user__is_active=True).count(),
        "active_buses":Bus.objects.filter(active=True,company__status=Company.Status.VERIFIED).count(),
        "future_departures":Departure.objects.filter(status=Departure.Status.PUBLISHED,company__status=Company.Status.VERIFIED,starts_at__gt=now).count(),
        "test_bookings":active.filter(booking__status=Booking.Status.TEST_PAID).values("booking_id").distinct().count(),
        "held_bookings":active.filter(booking__status=Booking.Status.HELD).values("booking_id").distinct().count(),
        "test_boardings":TestBoarding.objects.filter(leg__booking__status=Booking.Status.TEST_PAID).count(),
        "open_support":SupportRequest.objects.exclude(status=SupportRequest.Status.RESOLVED).count(),
        "real_payments_enabled":False,"real_amount":0,"generated_at":now.isoformat()
    })

@superuser_endpoint
def companies(request):
    qs=Company.objects.select_related("owner").order_by("-id")
    status=request.GET.get("status","")
    if status:
        if status not in Company.Status.values:raise ValueError("Statut invalide.")
        qs=qs.filter(status=status)
    for word in search_term(request).split():
        qs=qs.filter(Q(name__icontains=word)|Q(city__icontains=word)|Q(owner__first_name__icontains=word)|Q(owner__last_name__icontains=word)|Q(registration_number__icontains=word))
    rows,meta=page_slice(request,qs)
    return JsonResponse({"items":[{"id":c.pk,"name":c.name,"city":c.city,"status":c.status,"owner":c.owner.get_full_name() or c.owner.username,"created_at":c.created_at.isoformat()} for c in rows],**meta})

@superuser_endpoint
def travelers(request):
    qs=User.objects.filter(role=User.Role.TRAVELER,is_superuser=False).order_by("-id")
    status=request.GET.get("status","")
    if status not in ("","ACTIVE","INACTIVE"):raise ValueError("Statut invalide.")
    if status:qs=qs.filter(is_active=status=="ACTIVE")
    for word in search_term(request).split():
        qs=qs.filter(Q(first_name__icontains=word)|Q(last_name__icontains=word)|Q(phone__icontains=word)|Q(email__icontains=word))
    rows,meta=page_slice(request,qs)
    return JsonResponse({"items":[{"id":u.pk,"name":u.get_full_name() or u.username,"active":u.is_active,"created_at":u.date_joined.isoformat()} for u in rows],**meta})

@superuser_endpoint
def support(request):
    qs=SupportRequest.objects.select_related("requester").order_by("-id")
    status=request.GET.get("status","")
    if status:
        if status not in SupportRequest.Status.values:raise ValueError("Statut invalide.")
        qs=qs.filter(status=status)
    for word in search_term(request).split():
        qs=qs.filter(Q(subject__icontains=word)|Q(requester__first_name__icontains=word)|Q(requester__last_name__icontains=word))
    rows,meta=page_slice(request,qs)
    return JsonResponse({"items":[{"id":t.pk,"reference":str(t),"subject":t.subject,"status":t.status,"requester":t.requester.get_full_name() or t.requester.username,"created_at":t.created_at.isoformat()} for t in rows],**meta})
