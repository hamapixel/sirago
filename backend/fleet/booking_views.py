from datetime import timedelta
from uuid import UUID
from django.db import transaction
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_GET, require_POST
from accounts.models import Company, User
from accounts.views import data, error
from .models import Booking, BookingLeg, Departure
from .public_views import public_departures, public_row, bounded_int

def selection(values):
    out=bounded_int(values.get("out", ""),1,2**63-1)
    ret=bounded_int(values["ret"],1,2**63-1) if values.get("ret") else None
    count=bounded_int(values.get("count","1"),1,10)
    if out==ret:
        raise ValueError("Départs distincts requis.")
    return [out]+([ret] if ret else []),count

def selected_rows(ids,count,now):
    rows={d.id:d for d in public_departures(now).select_related("company","route","bus").filter(id__in=ids)}
    if len(rows)!=len(ids):
        raise ValueError("Un départ n’est plus disponible.")
    trips=[rows[i] for i in ids]
    if any(d.remaining<count for d in trips):
        raise ValueError("Le nombre de places restantes est insuffisant.")
    if len(trips)==2:
        a,b=trips
        if a.route.origin!=b.route.destination or a.route.destination!=b.route.origin or b.starts_at<a.ends_at:
            raise ValueError("Le trajet retour ne correspond pas à l’aller.")
    return trips

def quote_json(rows,count):
    return {"trips":[public_row(d) for d in rows],"count":count,"total":sum(d.price for d in rows)*count}

@never_cache
@require_GET
def quote(request):
    try:
        ids,count=selection(request.GET)
        return JsonResponse(quote_json(selected_rows(ids,count,timezone.now()),count))
    except (ValueError,TypeError,OverflowError):
        return error("Ce voyage n’est plus disponible ou la sélection est invalide.",409)

def booking_json(b):
    now=timezone.now()
    legs=list(b.legs.select_related("departure__route","departure__company").order_by("position"))
    return {"id":b.id,"reference":str(b.request_id),"count":b.passengers,"status":"EXPIRED" if b.status==Booking.Status.HELD and b.expires_at<=now else b.status,"expires_at":b.expires_at.isoformat(),
            "total":sum(l.unit_price for l in legs)*b.passengers,
            "trips":[{"id":l.departure_id,"company":l.departure.company.name,"origin":l.departure.route.origin,"destination":l.departure.route.destination,"starts_at":l.departure.starts_at.isoformat(),"price":l.unit_price} for l in legs]}

def traveler_error(request):
    if not request.user.is_authenticated:
        return error("Connectez-vous pour réserver.",401)
    if request.user.is_superuser or request.user.role!=User.Role.TRAVELER:
        return error("Un compte voyageur est requis.",403)
    return None

@never_cache
@csrf_protect
@require_POST
def reserve(request):
    denied=traveler_error(request)
    if denied is not None:return denied
    try:
        v=data(request)
        ids,count=selection(v)
        key=UUID(str(v.get("request_id","")))
        expected=v.get("total")
        if type(expected) is not int or expected<1:
            raise ValueError("Total invalide.")
        with transaction.atomic():
            # Serialize retries per traveler and writes with company management.
            User.objects.select_for_update().get(pk=request.user.pk)
            old=Booking.objects.filter(traveler=request.user,request_id=key).first()
            if old:
                if list(old.legs.order_by("position").values_list("departure_id",flat=True))!=ids or old.passengers!=count:
                    return error("Référence de requête déjà utilisée.",409)
                return JsonResponse(booking_json(old))
            company_ids=list(Departure.objects.filter(pk__in=ids).values_list("company_id",flat=True).distinct())
            list(Company.objects.select_for_update().filter(pk__in=company_ids).order_by("pk"))
            now=timezone.now()
            rows=selected_rows(ids,count,now)
            total=sum(d.price for d in rows)*count
            if total!=expected:
                return error("Le tarif a changé. Actualisez le récapitulatif.",409)
            if Booking.objects.filter(traveler=request.user,status=Booking.Status.HELD,expires_at__gt=now).count()>=3:
                return error("Vous avez déjà trois réservations en attente. Annulez-en une ou attendez son expiration.",409)
            expiry=min(now+timedelta(minutes=15),*(d.starts_at for d in rows))
            b=Booking.objects.create(traveler=request.user,request_id=key,passengers=count,expires_at=expiry)
            BookingLeg.objects.bulk_create([BookingLeg(booking=b,departure=d,position=i,unit_price=d.price) for i,d in enumerate(rows)])
            return JsonResponse(booking_json(b),status=201)
    except (ValueError,TypeError,OverflowError) as exc:
        return error(str(exc),409)

@never_cache
@require_GET
def mine(request):
    denied=traveler_error(request)
    if denied is not None:return denied
    try:
        page=bounded_int(request.GET.get("page","1"),1,10000)
    except ValueError:
        return error("Page invalide.")
    offset=(page-1)*30
    rows=list(Booking.objects.filter(traveler=request.user).order_by("-id")[offset:offset+31])
    return JsonResponse({"items":[booking_json(b) for b in rows[:30]],"has_next":len(rows)>30})

@never_cache
@csrf_protect
@require_POST
def cancel(request,pk):
    denied=traveler_error(request)
    if denied is not None:return denied
    with transaction.atomic():
        b=Booking.objects.select_for_update().filter(pk=pk,traveler=request.user).first()
        if not b:return error("Réservation introuvable.",404)
        if b.status==Booking.Status.HELD:
            b.status=Booking.Status.CANCELLED
            b.save(update_fields=["status"])
        return JsonResponse(booking_json(b))
