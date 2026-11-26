"""Atomic full or partial rescheduling of one leg, local TEST only."""
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

def eligible(b,now,position):
    if b.status!=Booking.Status.TEST_PAID or not hasattr(b,"simulated_payment"):
        raise ValueError("Seule une réservation payée en simulation peut être reportée.")
    legs=list(b.legs.select_related("departure__route","departure__company").order_by("position"))
    if len(legs) not in (1,2) or type(position) is not int or not 0<=position<len(legs):raise ValueError("Trajet à reporter invalide.")
    if any(l.departure.company.status!=Company.Status.VERIFIED for l in legs):raise ValueError("Compagnie indisponible.")
    if any(l.departure.starts_at<=now for l in legs):raise ValueError("Le voyage a déjà commencé.")
    if TestBoarding.objects.filter(leg__booking=b).exists():raise ValueError("Un passager a déjà embarqué. Report impossible.")
    if any(not public_departures(now).filter(pk=l.departure_id).exists() for l in legs if l.position!=position):
        raise ValueError("L’autre trajet n’est plus disponible. Contactez la compagnie.")
    return legs,legs[position]

def positions(b,raw):
    if raw is None:return list(range(b.passengers))
    if not isinstance(raw,list) or not 1<=len(raw)<=b.passengers or any(type(i) is not int or not 0<=i<b.passengers for i in raw) or len(set(raw))!=len(raw):
        raise ValueError("Sélection de passagers invalide.")
    return sorted(raw)

def counts(leg,selected):
    premium=sum(i in leg.premium_positions for i in selected)
    return len(selected)-premium,premium

def choices(legs,leg,now,selected):
    d=leg.departure
    standard,premium=counts(leg,selected)
    qs=public_departures(now).filter(company_id=d.company_id,route_id=d.route_id,
        standard_remaining__gte=standard,premium_remaining__gte=premium).exclude(pk=d.pk)
    if len(legs)==2:
        if leg.position==0:qs=qs.filter(ends_at__lte=legs[1].departure.starts_at)
        else:qs=qs.filter(starts_at__gte=legs[0].departure.ends_at)
    return qs.select_related("company","bus","route").order_by("starts_at","id")

def amount_for(leg,selected,standard_price,premium_price):
    standard,premium=counts(leg,selected)
    return standard*standard_price+premium*premium_price

def issue(b,legs,selected,changed_position=None,target=None):
    new=Booking.objects.create(traveler=b.traveler,request_id=uuid4(),passengers=len(selected),
        passenger_names=[b.passenger_names[i] if i<len(b.passenger_names) else f"Passager {i+1}" for i in selected],
        ticket_mode=b.ticket_mode,status=Booking.Status.TEST_PAID,
        expires_at=min(target.starts_at if l.position==changed_position else l.departure.starts_at for l in legs))
    new_legs=[]
    for leg in legs:
        changed=leg.position==changed_position
        d=target if changed else leg.departure
        premium_positions=[j for j,i in enumerate(selected) if i in leg.premium_positions]
        standard_price=d.price if changed else leg.unit_price
        premium_price=d.premium_price if changed else leg.premium_unit_price
        new_legs.append(BookingLeg.objects.create(booking=new,departure=d,position=leg.position,unit_price=standard_price,premium_count=len(premium_positions),
            premium_unit_price=premium_price if premium_positions else 0,premium_positions=premium_positions))
    SimulatedPayment.objects.create(booking=new,amount=sum(l.total for l in new_legs),network=b.simulated_payment.network)
    register_refs(new,new_legs)
    return new

def result(row):
    return {**booking_json(row.replacement),"retained_booking":booking_json(row.retained) if row.retained_id else None}

@never_cache
@require_GET
def options(request,pk):
    denied=access(request,pk)
    if denied is not None:return denied
    b=Booking.objects.filter(pk=pk,traveler=request.user).first()
    if b is None:return error("Réservation introuvable.",404)
    try:
        now=timezone.now()
        position=int(request.GET.get("leg","0"))
        legs,leg=eligible(b,now,position)
        raw=request.GET.get("passengers")
        selected=positions(b,[int(i) for i in raw.split(",")] if raw is not None else None)
        previous_amount=amount_for(leg,selected,leg.unit_price,leg.premium_unit_price)
        qs=choices(legs,leg,now,selected)
        day=request.GET.get("date","")
        if day:
            day=date.fromisoformat(day)
            start=datetime.combine(day,time.min,TZ)
            qs=qs.filter(starts_at__gte=start,starts_at__lt=start+timedelta(days=1))
        rows,meta=page_slice(request,qs)
        return JsonResponse({"previous_amount":previous_amount,"items":[{**public_row(d),"total":amount_for(leg,selected,d.price,d.premium_price),"difference":amount_for(leg,selected,d.price,d.premium_price)-previous_amount} for d in rows],**meta})
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
        position=values.get("leg",0)
        if type(position) is not int or position not in (0,1):return error("Trajet à reporter invalide.",400)
        if type(target) is not int or not 1<=target<=2**63-1 or type(expected) is not int or expected<1:
            return error("Départ ou montant invalide.",400)
        with transaction.atomic():
            User.objects.select_for_update().get(pk=request.user.pk)
            b=Booking.objects.select_for_update().filter(pk=pk,traveler=request.user).first()
            if b is None:return error("Réservation introuvable.",404)
            selected=positions(b,values.get("passengers"))
            previous=TestTicketReport.objects.filter(original=b).select_related("replacement","retained").first()
            if previous:
                if (previous.selected_positions or list(range(b.passengers)))!=selected or previous.new_amount!=expected or not previous.replacement.legs.filter(position=position,departure_id=target).exists() or b.legs.filter(position=position,departure_id=target).exists():
                    return error("Cette réservation a déjà été reportée.",409)
                return JsonResponse(result(previous))
            # Same company lock as reservation, departure updates and boarding.
            company_ids=list(b.legs.values_list("departure__company_id",flat=True).distinct())
            list(Company.objects.select_for_update().filter(pk__in=company_ids).order_by("pk"))
            now=timezone.now()
            legs,leg=eligible(b,now,position)
            d=choices(legs,leg,now,selected).filter(pk=target).first()
            if not d:return error("Départ ou catégorie de places indisponible.",409)
            amount=amount_for(leg,selected,d.price,d.premium_price)
            if expected!=amount:return error("Le tarif a changé. Actualisez les départs.",409)
            remaining=[i for i in range(b.passengers) if i not in selected]
            # A retained group must still have a valid published departure.
            if remaining and not public_departures(now).filter(pk=leg.departure_id).exists():
                return error("Le départ initial n’est plus disponible. Reportez tous les passagers.",409)
            new=issue(b,legs,selected,position,d)
            retained=issue(b,legs,remaining) if remaining else None
            row=TestTicketReport.objects.create(original=b,replacement=new,retained=retained,selected_positions=selected,
                previous_amount=amount_for(leg,selected,leg.unit_price,leg.premium_unit_price),new_amount=amount)
            b.status=Booking.Status.REPORTED
            b.save(update_fields=["status"])
            message=f"{d.route.origin} → {d.route.destination} : {len(selected)} passager(s), nouveau départ le {d.starts_at.astimezone(TZ):%d/%m/%Y à %H:%M}. Aucun débit ni remboursement réel."
            if retained:message+=f" {len(remaining)} passager(s) restent au départ initial, avec de nouveaux billets."
            notify(b.traveler_id,"TEST_REPORT","Billets reportés en mode TEST",message)
            for owner_id in {l.departure.company.owner_id for l in legs}:
                notify(owner_id,"TEST_REPORT","Report de réservation TEST",message)
            return JsonResponse(result(row),status=201)
    except (ValueError,TypeError,OverflowError) as exc:return error(str(exc),409)
