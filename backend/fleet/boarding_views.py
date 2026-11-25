from accounts.notifications import notify
import re
from datetime import date
from django.db.models import Q, F, Func, TextField
from .listing import search_term, page_slice
from django.http import JsonResponse
from django.utils import timezone
from accounts.models import Company
from accounts.views import data,error
from .booking_views import simulation_enabled
from .models import Booking,Departure,TestTicketReference,TestBoarding
from .ticket_refs import ticket_groups,ticket_code
from .views import company_endpoint

def access(request,company,method):
    if not simulation_enabled():return error("Contrôle TEST indisponible.",404)
    if request.method!=method:return error("Méthode non autorisée.",405)
    if company.status!=Company.Status.VERIFIED:return error("Compagnie non validée.",403)
    return None

def resolve(company,code):
    if not isinstance(code,str) or not re.fullmatch(r"SRG-TEST-[0-9A-F]{32}",code.strip().upper()):
        return None,None,error("Référence de billet TEST invalide.",400)
    ref=TestTicketReference.objects.select_related("leg__booking","leg__departure__route").filter(
        code=code.strip().upper(),leg__departure__company=company,
        leg__booking__status=Booking.Status.TEST_PAID,
        leg__booking__simulated_payment__isnull=False).first()
    if not ref:return None,None,error("Billet introuvable pour cette compagnie.",404)
    leg=ref.leg
    indices=next((g for g in ticket_groups(leg.booking,leg) if g[0]==ref.anchor),None)
    if not indices or ticket_code(leg.booking,leg,indices)!=ref.code:
        return None,None,error("Billet incohérent.",409)
    return ref,indices,None

def row(ref,indices):
    l=ref.leg;b=l.booking;d=l.departure
    boarded={r.passenger:r.boarded_at.isoformat() for r in TestBoarding.objects.filter(leg=l,passenger__in=indices)}
    return {"code":ref.code,"origin":d.route.origin,"destination":d.route.destination,
        "starts_at":d.starts_at.isoformat(),"boarding_point":d.route.boarding_point,
        "category":"Premium" if indices[0] in l.premium_positions else "Standard",
        "count":len(indices),"boarded":len(boarded),"remaining":len(indices)-len(boarded),
        "can_board":d.status==Departure.Status.PUBLISHED and timezone.now()<d.ends_at,
        "passengers":[{"index":i,"name":b.passenger_names[i] if i<len(b.passenger_names) else f"Passager {i+1}","boarded_at":boarded.get(i)} for i in indices]}

@company_endpoint
def lookup(request,company):
    denied=access(request,company,"POST")
    if denied is not None:return denied
    ref,indices,denied=resolve(company,data(request).get("code"))
    if denied is not None:return denied
    return JsonResponse(row(ref,indices))

@company_endpoint
def validate(request,company):
    denied=access(request,company,"POST")
    if denied is not None:return denied
    values=data(request)
    ref,indices,denied=resolve(company,values.get("code"))
    if denied is not None:return denied
    selected=values.get("passengers")
    if not isinstance(selected,list) or not 1<=len(selected)<=100 or any(type(i) is not int or i not in indices for i in selected) or len(set(selected))!=len(selected):
        return error("Sélection de passagers invalide.",400)
    if not row(ref,indices)["can_board"]:return error("Départ indisponible ou terminé.",409)
    # Company row locked by company_endpoint; database unique constraint is final guard.
    added=0
    for i in selected:
        _,created=TestBoarding.objects.get_or_create(leg=ref.leg,passenger=i,defaults={"actor":request.user})
        added+=int(created)
    if added:
        d=ref.leg.departure
        message=f"{d.route.origin} → {d.route.destination} : {added} passager(s) validé(s) en mode TEST."
        notify(ref.leg.booking.traveler_id,"TEST_BOARDING","Embarquement de test enregistré",message)
        notify(company.owner_id,"TEST_BOARDING","Contrôle de billets TEST",message)
    return JsonResponse(row(ref,indices))

@company_endpoint
def history(request,company):
    denied=access(request,company,"GET")
    if denied is not None:return denied
    qs=TestBoarding.objects.filter(leg__departure__company=company).select_related("leg__booking","leg__departure__route","actor").order_by("-boarded_at","-id")
    term=search_term(request)
    if term:
        # PostgreSQL JSON array extraction by passenger index (zero based).
        qs=qs.annotate(passenger_name=Func(F("leg__booking__passenger_names"),F("passenger"),template="(%(expressions)s)",arg_joiner=" ->> ",output_field=TextField()))
        for word in term.split():
            qs=qs.filter(Q(passenger_name__icontains=word)|Q(leg__departure__route__origin__icontains=word)|Q(leg__departure__route__destination__icontains=word)|Q(actor__first_name__icontains=word)|Q(actor__last_name__icontains=word))
    day=request.GET.get("date","")
    if day:qs=qs.filter(boarded_at__date=date.fromisoformat(day))
    rows,meta=page_slice(request,qs)
    return JsonResponse({"items":[{"id":r.id,"name":r.leg.booking.passenger_names[r.passenger] if r.passenger<len(r.leg.booking.passenger_names) else f"Passager {r.passenger+1}","origin":r.leg.departure.route.origin,"destination":r.leg.departure.route.destination,"boarded_at":r.boarded_at.isoformat(),"agent":r.actor.get_full_name() or "Agent","category":"Premium" if r.passenger in r.leg.premium_positions else "Standard"} for r in rows],**meta})
