"""Company-scoped, read-only detail of a single booking leg.

Never expose other companies' legs, payer contacts, QR secrets or payment identifiers.
"""
from django.http import JsonResponse
from django.utils import timezone
from accounts.models import Company
from accounts.views import error
from .models import Booking, BookingLeg, Departure, TestBoarding

def reservation_detail(request, company, pk):
    if company.status != Company.Status.VERIFIED:
        return error("Compagnie non validée.",403)
    if not 1 <= pk <= 2**63-1:
        return error("Réservation introuvable.",404)
    leg=BookingLeg.objects.select_related(
        "booking","booking__simulated_payment","booking__sandbox_checkout",
        "departure__route","departure__bus"
    ).filter(pk=pk,departure__company=company).first()
    if leg is None:
        return error("Réservation introuvable.",404)
    b=leg.booking
    d=leg.departure
    now=timezone.now()
    status="EXPIRED" if b.status==Booking.Status.HELD and b.expires_at<=now else b.status
    checkout=getattr(b,"sandbox_checkout",None)
    simulated=getattr(b,"simulated_payment",None)
    paid=status==Booking.Status.TEST_PAID and bool(simulated or (
        checkout and checkout.issued_at and checkout.status=="PAID" and checkout.transaction_id))
    method="SASPAY_SIMULATION" if paid and checkout and checkout.issued_at else "LOCAL_SIMULATION" if paid else "NONE"
    financial=not getattr(request,"company_agent",None)
    boarded={p.passenger:p.boarded_at.isoformat() for p in TestBoarding.objects.filter(leg=leg)}
    premium=set(leg.premium_positions)
    passengers=[]
    for i in range(b.passengers):
        at=boarded.get(i)
        state=("BOARDED" if at else "UNAVAILABLE" if status in ("EXPIRED","CANCELLED","REPORTED") or d.status==Departure.Status.CANCELLED else
               "PENDING" if not paid else "ABSENT" if d.status==Departure.Status.PUBLISHED and now>=d.ends_at else "WAITING")
        row={"index":i,"name":b.passenger_names[i] if i<len(b.passenger_names) else f"Passager {i+1}",
             "category":"Premium" if i in premium else "Standard","state":state,"boarded_at":at}
        if financial:row["amount"]=leg.premium_unit_price if i in premium else leg.unit_price
        passengers.append(row)
    result={"id":leg.pk,"reference":str(b.request_id),"company":company.name,
            "status":status,"departure_status":d.status,"created_at":b.created_at.isoformat(),
            "expires_at":b.expires_at.isoformat(),"position":leg.position,"origin":d.route.origin,
            "destination":d.route.destination,"boarding_point":d.route.boarding_point,
            "arrival_point":d.route.arrival_point,"starts_at":d.starts_at.isoformat(),
            "ends_at":d.ends_at.isoformat(),"bus_name":d.bus.name,"plate":d.bus.plate,
            "ticket_mode":b.ticket_mode,"payment_method":method,"count":b.passengers,
            "premium_count":leg.premium_count,"boarded_count":sum(p["state"]=="BOARDED" for p in passengers),
            "passengers":passengers}
    if financial:result.update(total=leg.total,real_amount=0,simulated_amount=leg.total if paid else 0)
    return JsonResponse(result)
