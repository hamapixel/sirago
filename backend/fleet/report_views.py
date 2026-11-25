"""Atomic whole-booking rescheduling, local TEST only."""
from datetime import date,datetime,time,timedelta
from uuid import uuid4
from django.db import transaction
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_GET,require_POST
from accounts.models import Company,User
from accounts.views import data,error
from accounts.notifications import notify
from .models import Booking,BookingLeg,SimulatedPayment,TestBoarding,TestTicketReport
from .booking_views import booking_json,simulation_enabled,traveler_error
from .public_views import public_departures,public_row
from .ticket_refs import register_refs
from .listing import page_slice
from .views import TZ

def access(request,pk):
    if not simulation_enabled():return error("Report TEST indisponible.",404)
    denied=traveler_error(request)
    if denied is not None:return denied
    if not 1<=pk<=2**63-1:return error("Réservation introuvable.",404)
    return None

def eligible(b,now):
    if b.status!=Booking.Status.TEST_PAID or not hasattr(b,"simulated_payment"):
        raise ValueError("Seule une réservation payée en simulation peut être reportée.")
    legs=list(b.legs.select_related("departure__route","departure__company"))
    if len(legs)!=1:raise ValueError("Le report aller-retour n’est pas encore disponible.")
    leg=legs[0]
    if leg.departure.company.status!=Company.Status.VERIFIED:raise ValueError("Compagnie indisponible.")
    if leg.departure.starts_at<=now:raise ValueError("Le départ a déjà commencé.")
    if TestBoarding.objects.filter(leg=leg).exists():raise ValueError("Un passager a déjà embarqué. Report impossible.")
    return leg

def choices(b,leg,now):
    d=leg.departure
    return public_departures(now).filter(company_id=d.company_id,route_id=d.route_id,
        standard_remaining__gte=b.passengers-leg.premium_count,premium_remaining__gte=leg.premium_count).exclude(pk=d.pk).select_related("company","bus","route").order_by("starts_at","id")

def total(b,leg,d):
    return (b.passengers-leg.premium_count)*d.price+leg.premium_count*d.premium_price

@never_cache
@require_GET
def options(request,pk):
    denied=access(request,pk)
    if denied is not None:return denied
    b=Booking.objects.filter(pk=pk,traveler=request.user).first()
    if b is None:return error("Réservation introuvable.",404)
    try:
        now=timezone.now()
        leg=eligible(b,now)
        qs=choices(b,leg,now)
        day=request.GET.get("date","")
        if day:
            day=date.fromisoformat(day)
            start=datetime.combine(day,time.min,TZ)
            qs=qs.filter(starts_at__gte=start,starts_at__lt=start+timedelta(days=1))
        rows,meta=page_slice(request,qs)
        return JsonResponse({"previous_amount":leg.total,"items":[{**public_row(d),"total":total(b,leg,d),"difference":total(b,leg,d)-leg.total} for d in rows],**meta})
    except (ValueError,OverflowError,TypeError) as exc:return error(str(exc),409)

@never_cache
@csrf_protect
@require_POST
def report(request,pk):
    denied=access(request,pk)
    if denied is not None:return denied
    try:
        values=data(request)
        target=values.get("departure_id")
        expected=values.get("total")
        if type(target) is not int or not 1<=target<=2**63-1 or type(expected) is not int or expected<1:
            return error("Départ ou montant invalide.",400)
        with transaction.atomic():
            User.objects.select_for_update().get(pk=request.user.pk)
            b=Booking.objects.select_for_update().filter(pk=pk,traveler=request.user).first()
            if b is None:return error("Réservation introuvable.",404)
            previous=TestTicketReport.objects.filter(original=b).select_related("replacement").first()
            if previous:
                if previous.new_amount!=expected or not previous.replacement.legs.filter(departure_id=target).exists():
                    return error("Cette réservation a déjà été reportée.",409)
                return JsonResponse(booking_json(previous.replacement))
            # Same company lock as reservation, departure updates and boarding.
            company_ids=list(b.legs.values_list("departure__company_id",flat=True).distinct())
            list(Company.objects.select_for_update().filter(pk__in=company_ids).order_by("pk"))
            now=timezone.now()
            leg=eligible(b,now)
            d=choices(b,leg,now).filter(pk=target).first()
            if not d:return error("Départ ou catégorie de places indisponible.",409)
            amount=total(b,leg,d)
            if expected!=amount:return error("Le tarif a changé. Actualisez les départs.",409)
            new=Booking.objects.create(traveler=b.traveler,request_id=uuid4(),passengers=b.passengers,
                passenger_names=b.passenger_names,ticket_mode=b.ticket_mode,status=Booking.Status.TEST_PAID,expires_at=d.starts_at)
            new_leg=BookingLeg.objects.create(booking=new,departure=d,position=0,unit_price=d.price,premium_count=leg.premium_count,
                premium_unit_price=d.premium_price if leg.premium_count else 0,premium_positions=leg.premium_positions)
            SimulatedPayment.objects.create(booking=new,amount=amount,network=b.simulated_payment.network)
            TestTicketReport.objects.create(original=b,replacement=new,previous_amount=leg.total,new_amount=amount)
            b.status=Booking.Status.REPORTED
            b.save(update_fields=["status"])
            register_refs(new,[new_leg])
            message=f"{d.route.origin} → {d.route.destination} : {b.passengers} passager(s), nouveau départ le {d.starts_at.astimezone(TZ):%d/%m/%Y à %H:%M}. Aucun débit ni remboursement réel."
            notify(b.traveler_id,"TEST_REPORT","Billets reportés en mode TEST",message)
            notify(d.company.owner_id,"TEST_REPORT","Report de réservation TEST",message)
            return JsonResponse(booking_json(new),status=201)
    except (ValueError,TypeError,OverflowError) as exc:return error(str(exc),409)
