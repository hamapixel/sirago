"""Read-only test allocations. No settlement balance or real funds."""
from datetime import date,timedelta,datetime,time
from django.db.models import Count,Sum,Q
from django.db.models.functions import Cast
from django.db.models import CharField
from django.http import JsonResponse
from django.utils import timezone
from fleet.models import SandboxCommission,SandboxCheckout,Booking
from fleet.listing import page_slice,search_term
from .supervision import superuser_endpoint

@superuser_endpoint
def ledger(request):
    qs=SandboxCommission.objects.filter(checkout__status="PAID",checkout__issued_at__isnull=False,checkout__transaction_id__isnull=False,leg__booking__status=Booking.Status.TEST_PAID)
    start=request.GET.get("date_from","")
    end=request.GET.get("date_to","")
    if bool(start)!=bool(end):raise ValueError("Période incomplète.")
    if start:
        a,b=date.fromisoformat(start),date.fromisoformat(end)
        if a>b or (b-a).days>366:raise ValueError("Période invalide.")
        tz=timezone.get_default_timezone()
        qs=qs.filter(checkout__issued_at__gte=datetime.combine(a,time.min,tzinfo=tz),checkout__issued_at__lt=datetime.combine(b+timedelta(days=1),time.min,tzinfo=tz))
    for word in search_term(request).split():
        qs=qs.annotate(reference_search=Cast("leg__booking__request_id",CharField())).filter(Q(company__name__icontains=word)|Q(leg__departure__route__origin__icontains=word)|Q(leg__departure__route__destination__icontains=word)|Q(reference_search__icontains=word))
    summary=qs.aggregate(gross=Sum("gross",default=0),commission=Sum("commission",default=0),company_share=Sum("company_share",default=0),unconfigured=Sum("gross",filter=Q(rate_bps__isnull=True),default=0),unconfigured_count=Count("id",filter=Q(rate_bps__isnull=True)))
    rows,meta=page_slice(request,qs.select_related("company","checkout","leg__booking","leg__departure__route").order_by("-checkout__issued_at","-id"))
    items=[{"id":r.pk,"company":r.company.name,"reference":str(r.leg.booking.request_id),"route":f"{r.leg.departure.route.origin} → {r.leg.departure.route.destination}","issued_at":r.checkout.issued_at.isoformat(),"gross":r.gross,"rate_bps":r.rate_bps,"commission":r.commission,"company_share":r.company_share} for r in rows]
    legacy=SandboxCheckout.objects.filter(status="PAID",issued_at__isnull=False,commission_lines__isnull=True).count()
    return JsonResponse({"items":items,"summary":summary,"legacy_count":legacy,**meta})
