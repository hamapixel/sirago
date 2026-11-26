from datetime import date, datetime, time, timedelta
import unicodedata
from django.db.models import F, Min, Q, Count
from django.http import JsonResponse
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET
from accounts.models import Company
from accounts.views import error
from .models import Departure
from .availability import with_remaining
from .views import TZ
from .localities import valid_localities, locality_names

def public_departures(now):
    return with_remaining(Departure.objects.filter(
        status=Departure.Status.PUBLISHED, starts_at__gt=now,
        company__status=Company.Status.VERIFIED, bus__active=True, route__active=True,
        bus__company_id=F("company_id"), route__company_id=F("company_id"),
        capacity__lte=F("bus__capacity"),
        premium_capacity__lte=F("bus__premium_capacity"),
    ).filter(
        capacity__lte=F("bus__capacity")-F("bus__premium_capacity")+F("premium_capacity"),
    ), now)

def minimum_total(d,count):
    premium=max(0,count-d.standard_remaining)
    return (count-premium)*d.price+premium*d.premium_price

def public_row(d):
    return {
        "id":d.id, "company_id":d.company_id, "company":d.company.name,
        "bus_name":d.bus.name, "origin":d.route.origin, "destination":d.route.destination,
        "boarding_point":d.route.boarding_point, "arrival_point":d.route.arrival_point,
        "starts_at":d.starts_at.isoformat(), "ends_at":d.ends_at.isoformat(),
        "duration_minutes":int((d.ends_at-d.starts_at).total_seconds()//60),
        "price":d.price, "capacity":d.capacity, "remaining":max(0,d.remaining),"standard_remaining":max(0,d.standard_remaining),"premium_remaining":max(0,d.premium_remaining),"premium_price":d.premium_price,"from_price":d.from_price,
    }

def bounded_int(raw, low, high):
    value=int(raw)
    if not low<=value<=high:
        raise ValueError("Valeur hors limites.")
    return value

@never_cache
@require_GET
def search(request):
    now=timezone.now()
    today=now.astimezone(TZ).date()
    q=request.GET
    origin=q.get("origin","")
    destination=q.get("destination","")
    if not valid_localities(origin,destination):
        return error("Choisissez deux villes différentes.")
    try:
        day=date.fromisoformat(q.get("date",""))
        if not today<=day<=today+timedelta(days=365):
            raise ValueError("Choisissez une date dans les 365 prochains jours.")
        passengers=bounded_int(q.get("passengers","1"),1,100)
        page=bounded_int(q.get("page","1"),1,1000)
        max_price=bounded_int(q.get("max_price","1000000"),1,1000000)
        company=q.get("company","").strip()
        if len(company)>150:
            raise ValueError("Nom de compagnie trop long.")
        period=q.get("period","")
        periods={"":(0,24),"morning":(0,12),"afternoon":(12,18),"evening":(18,24)}
        sort=q.get("sort","price")
        orders={"price":("from_price","starts_at","id"),"departure":("starts_at","price","id"),"duration":("duration","starts_at","id")}
        if period not in periods or sort not in orders:
            raise ValueError("Filtre invalide.")
        start=datetime.combine(day,time.min,TZ)
        low,high=periods[period]
        qs=public_departures(now).filter(route__origin=origin,route__destination=destination,
            starts_at__gte=start+timedelta(hours=low),starts_at__lt=start+timedelta(hours=high),
            remaining__gte=passengers,from_price__lte=max_price).filter(Q(standard_remaining__gte=passengers)|Q(premium_price__lte=max_price))
        if q.get("after"):
            after=parse_datetime(q["after"])
            if after is None or timezone.is_naive(after):
                raise ValueError("Horaire de correspondance invalide.")
            qs=qs.filter(starts_at__gte=after)
        options=list(qs.order_by().values("company_id","company__name").annotate(departures=Count("id")).order_by("company__name","company_id"))
        if company:qs=qs.filter(company__name__icontains=company)
        if q.get("company_id"):qs=qs.filter(company_id=bounded_int(q["company_id"],1,2**63-1))
        qs=qs.annotate(duration=F("ends_at")-F("starts_at")).select_related("company","route","bus").order_by(*orders[sort])
        total=qs.count()
        offset=(page-1)*20
        rows=list(qs[offset:offset+20])
        return JsonResponse({"items":[public_row(d) for d in rows],"total":total,"page":page,"has_next":offset+len(rows)<total,"companies":[{"id":c["company_id"],"name":c["company__name"],"departures":c["departures"]} for c in options]})
    except (ValueError, OverflowError):
        return error("Vérifiez la date, les passagers et les filtres de recherche.")

@never_cache
@require_GET
def home(request):
    qs=public_departures(timezone.now()).filter(remaining__gt=0)
    popular=list(qs.values("route__origin","route__destination").annotate(price=Min("from_price")).order_by("route__origin","route__destination")[:12])
    partners=list(qs.values("company_id","company__name","company__city").distinct().order_by("company__name","company_id")[:30])
    return JsonResponse({
        "routes":[{"origin":r["route__origin"],"destination":r["route__destination"],"price":r["price"]} for r in popular],
        "companies":[{"id":r["company_id"],"name":r["company__name"],"city":r["company__city"]} for r in partners],
    })


def normalized_city(value):
    return "".join(c for c in unicodedata.normalize("NFD", value.casefold()) if not unicodedata.combining(c)).strip()

@never_cache
@require_GET
def partner(request, pk):
    if not 1 <= pk <= 2**63-1:
        return error("Compagnie introuvable.",404)
    company=Company.objects.filter(pk=pk,status=Company.Status.VERIFIED).first()
    if not company:
        return error("Compagnie introuvable.",404)
    now=timezone.now()
    today=now.astimezone(TZ).date()
    try:
        raw_date=request.GET.get("date","")
        day=date.fromisoformat(raw_date) if raw_date else None
        if day is not None and not today<=day<=today+timedelta(days=365):
            raise ValueError("Date invalide.")
        count=bounded_int(request.GET.get("passengers","1"),1,100)
        page=bounded_int(request.GET.get("page","1"),1,1000)
        term=request.GET.get("q","").strip()
        if len(term)>100:
            raise ValueError("Recherche trop longue.")
        qs=public_departures(now).filter(company_id=company.pk,remaining__gte=count)
        if term:
            matching=[city for city in locality_names() if normalized_city(term) in normalized_city(city)]
            qs=qs.filter(Q(route__origin__in=matching)|Q(route__destination__in=matching))
        last=datetime.combine(today+timedelta(days=366),time.min,TZ)
        qs=qs.filter(starts_at__lt=last)
        if day is not None:
            start=datetime.combine(day,time.min,TZ)
            day_qs=qs.filter(starts_at__gte=start,starts_at__lt=start+timedelta(days=1))
        else:
            day_qs=qs
        day_qs=day_qs.select_related("company","route","bus").order_by("route__origin","route__destination","starts_at","id")
        total=day_qs.count()
        offset=(page-1)*20
        rows=list(day_qs[offset:offset+20])
        next_date=None
        if not total and day is not None:
            future=qs.filter(starts_at__gte=start+timedelta(days=1),starts_at__lt=last).order_by("starts_at").values_list("starts_at",flat=True).first()
            if future:next_date=future.astimezone(TZ).date().isoformat()
        return JsonResponse({"company":{"id":company.pk,"name":company.name,"city":company.city},"items":[public_row(d) for d in rows],"total":total,"page":page,"has_next":offset+len(rows)<total,"next_date":next_date})
    except (ValueError,OverflowError):
        return error("Vérifiez la date, la recherche et les passagers.")
