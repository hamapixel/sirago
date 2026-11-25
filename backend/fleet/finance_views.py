"""Operational booking values by departure date; never a cash ledger."""
from datetime import date, datetime, time, timedelta
from django.db.models import BigIntegerField, ExpressionWrapper, F, Q, Sum, Count
from django.http import JsonResponse
from django.utils import timezone
from accounts.models import Company
from accounts.views import error
from .availability import active_legs
from .listing import page_slice,search_term
from .models import Booking
from .views import company_endpoint,TZ

def metrics():
    paid=Q(booking__status=Booking.Status.TEST_PAID,booking__simulated_payment__isnull=False)
    pending=Q(booking__status=Booking.Status.HELD)
    return {
        "simulated_amount":Sum("leg_amount",filter=paid,default=0),
        "pending_amount":Sum("leg_amount",filter=pending,default=0),
        "simulated_passengers":Sum("booking__passengers",filter=paid,default=0),
        "pending_passengers":Sum("booking__passengers",filter=pending,default=0),
        "standard":Sum(F("booking__passengers")-F("premium_count"),filter=paid,default=0),
        "premium":Sum("premium_count",filter=paid,default=0),
        "orange_amount":Sum("leg_amount",filter=paid & Q(booking__simulated_payment__network="orange_ml"),default=0),
        "moov_amount":Sum("leg_amount",filter=paid & Q(booking__simulated_payment__network="moov_ml"),default=0),
    }

@company_endpoint
def finance(request,company):
    if request.method!="GET":return error("Méthode non autorisée.",405)
    if company.status!=Company.Status.VERIFIED:return error("Compagnie non validée.",403)
    now=timezone.now();today=now.astimezone(TZ).date()
    first=date.fromisoformat(request.GET.get("date_from",today.replace(day=1).isoformat()))
    last=date.fromisoformat(request.GET.get("date_to",today.isoformat()))
    if last<first or (last-first).days>365:return error("Choisissez une période de 366 jours maximum.")
    qs=active_legs(now).filter(departure__company=company,
        departure__starts_at__gte=datetime.combine(first,time.min,TZ),
        departure__starts_at__lt=datetime.combine(last+timedelta(days=1),time.min,TZ))
    for word in search_term(request).split():
        qs=qs.filter(Q(departure__route__origin__icontains=word)|Q(departure__route__destination__icontains=word)|Q(departure__bus__name__icontains=word)|Q(departure__bus__plate__icontains=word))
    qs=qs.annotate(leg_amount=ExpressionWrapper(F("unit_price")*(F("booking__passengers")-F("premium_count"))+F("premium_unit_price")*F("premium_count"),output_field=BigIntegerField()))
    summary=qs.aggregate(**metrics(),departures=Count("departure_id",distinct=True))
    groups=qs.values("departure_id","departure__starts_at","departure__route__origin","departure__route__destination","departure__bus__name").annotate(**metrics()).order_by("-departure__starts_at","-departure_id")
    rows,meta=page_slice(request,groups)
    return JsonResponse({"date_from":first.isoformat(),"date_to":last.isoformat(),"real_payments_enabled":False,"summary":{**summary,"real_amount":0},"items":[{"id":r["departure_id"],"starts_at":r["departure__starts_at"].isoformat(),"origin":r["departure__route__origin"],"destination":r["departure__route__destination"],"bus":r["departure__bus__name"],**{k:r[k] for k in metrics()},"real_amount":0} for r in rows],**meta})
