from datetime import date, datetime, time, timedelta
from functools import wraps
from zoneinfo import ZoneInfo
from django.db import IntegrityError, transaction
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods
from accounts.models import Company, User
from accounts.views import data, field, error
from .models import Bus, Route, Departure
from .availability import active_legs, with_remaining

CITIES = ["Bamako","Sikasso","Kayes","Ségou","Koutiala","Bougouni","Mopti","San","Kita"]
TZ = ZoneInfo("Africa/Bamako")
D = Departure.Status

def company_endpoint(fn):
    @never_cache
    @csrf_protect
    @require_http_methods(["GET","POST"])
    @wraps(fn)
    def wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return error("Connexion requise.",401)
        if request.user.is_superuser or request.user.role != User.Role.COMPANY:
            return error("Accès réservé aux compagnies.",403)
        try:
            with transaction.atomic():
                qs = Company.objects
                if request.method == "POST":
                    qs = qs.select_for_update()
                company = qs.filter(owner=request.user).first()
                if not company:
                    return error("Compagnie introuvable.",403)
                if request.method == "POST" and company.status not in (Company.Status.PENDING, Company.Status.VERIFIED):
                    return error("Votre compagnie ne peut pas effectuer de modification.",403)
                return fn(request, company, *args, **kwargs)
        except (ValueError, OverflowError) as exc:
            return error(str(exc))
        except IntegrityError:
            return error("Ces informations sont déjà utilisées ou invalides.",409)
    return wrapped

def integer(v, key, low, high):
    x = v.get(key)
    if type(x) is not int or not low <= x <= high:
        raise ValueError(f"{key} : saisissez un entier entre {low} et {high}.")
    return x

def flag(v, key, default=True):
    x = v.get(key, default)
    if type(x) is not bool:
        raise ValueError("Statut invalide.")
    return x

def bus_json(b):
    return {"id":b.id,"name":b.name,"plate":b.plate,"capacity":b.capacity,"premium_capacity":b.premium_capacity,"active":b.active}

def route_json(r):
    return {"id":r.id,"origin":r.origin,"destination":r.destination,"boarding_point":r.boarding_point,"arrival_point":r.arrival_point,"duration_minutes":r.duration_minutes,"price":r.price,"active":r.active}

def departure_json(d):
    return {"id":d.id,"bus_id":d.bus_id,"bus_name":d.bus.name,"route_id":d.route_id,"origin":d.route.origin,"destination":d.route.destination,"starts_at":d.starts_at.isoformat(),"ends_at":d.ends_at.isoformat(),"capacity":d.capacity,"premium_capacity":d.premium_capacity,"premium_price":d.premium_price,"price":d.price,"status":d.status}

def future_departures(qs):
    return qs.exclude(status=D.CANCELLED).filter(ends_at__gt=timezone.now())

@company_endpoint
def overview(request, company):
    if request.method != "GET":
        return error("Méthode non autorisée.",405)
    today = timezone.now().astimezone(TZ).date()
    start = datetime.combine(today,time.min,TZ)
    departures = company.departures.filter(starts_at__gte=start, starts_at__lt=start+timedelta(days=1),status=D.PUBLISHED)
    return JsonResponse({"status":company.status,"active_buses":company.buses.filter(active=True).count(),"active_routes":company.routes.filter(active=True).count(),"today_departures":departures.count(),"today_capacity":sum(with_remaining(departures.filter(starts_at__gt=timezone.now()),timezone.now()).values_list("remaining",flat=True))})

@company_endpoint
def buses(request,company,pk=None):
    if request.method == "GET":
        if pk is not None:
            return error("Méthode non autorisée.",405)
        return JsonResponse({"items":[bus_json(b) for b in company.buses.order_by("name","id")]})
    v=data(request)
    b=company.buses.filter(pk=pk).first() if pk is not None else Bus(company=company)
    if b is None:
        return error("Car introuvable.",404)
    name=field(v,"name",100)
    plate=" ".join(field(v,"plate",40).upper().split())
    capacity=integer(v,"capacity",1,100)
    premium=integer({"premium_capacity":v.get("premium_capacity",b.premium_capacity if pk is not None else 0)},"premium_capacity",0,capacity-1)
    active=flag(v,"active")
    if pk is not None and future_departures(b.departures).exists() and (not active or capacity!=b.capacity or premium!=b.premium_capacity):
        return error("Annulez les départs à venir avant de désactiver le car ou modifier sa capacité.",409)
    b.name,b.plate,b.capacity,b.premium_capacity,b.active=name,plate,capacity,premium,active
    b.save()
    return JsonResponse(bus_json(b),status=201 if pk is None else 200)

@company_endpoint
def routes(request,company,pk=None):
    if request.method=="GET":
        if pk is not None:
            return error("Méthode non autorisée.",405)
        return JsonResponse({"items":[route_json(r) for r in company.routes.order_by("origin","destination","id")]})
    v=data(request)
    r=company.routes.filter(pk=pk).first() if pk is not None else Route(company=company)
    if r is None:
        return error("Trajet introuvable.",404)
    origin=field(v,"origin",100)
    destination=field(v,"destination",100)
    if origin not in CITIES or destination not in CITIES or origin==destination:
        raise ValueError("Sélectionnez deux villes différentes.")
    boarding=field(v,"boarding_point",200)
    arrival=field(v,"arrival_point",200)
    duration=integer(v,"duration_minutes",1,2880)
    price=integer(v,"price",1,1000000)
    active=flag(v,"active")
    if pk is not None and future_departures(r.departures).exists() and (not active or (origin,destination,boarding,arrival,duration)!=(r.origin,r.destination,r.boarding_point,r.arrival_point,r.duration_minutes)):
        return error("Annulez les départs à venir avant de modifier le trajet ou le désactiver.",409)
    r.origin,r.destination,r.boarding_point,r.arrival_point,r.duration_minutes,r.price,r.active=origin,destination,boarding,arrival,duration,price,active
    r.save()
    return JsonResponse(route_json(r),status=201 if pk is None else 200)

def plan_dates(v):
    first=date.fromisoformat(field(v,"date",10))
    clock=time.fromisoformat(field(v,"time",5))
    if clock.tzinfo is not None:
        raise ValueError("Heure locale requise.")
    frequency=v.get("frequency","once")
    if frequency not in ("once","daily","weekly"):
        raise ValueError("Fréquence invalide.")
    end=first if frequency=="once" else date.fromisoformat(field(v,"end_date",10))
    if not 0 <= (end-first).days <= 30:
        raise ValueError("Choisissez une période de 31 jours maximum.")
    if first < timezone.now().astimezone(TZ).date() or end > timezone.now().astimezone(TZ).date()+timedelta(days=365):
        raise ValueError("Choisissez des dates futures dans les 365 prochains jours.")
    days=v.get("weekdays",[])
    if frequency=="weekly" and (not isinstance(days,list) or not days or any(type(x) is not int or not 0<=x<=6 for x in days)):
        raise ValueError("Sélectionnez les jours de départ.")
    starts=[datetime.combine(first+timedelta(days=i),clock,TZ) for i in range((end-first).days+1) if frequency!="weekly" or (first+timedelta(days=i)).weekday() in days]
    if not starts or any(s<=timezone.now() for s in starts):
        raise ValueError("Tous les départs doivent être dans le futur.")
    return starts

@company_endpoint
def departures(request,company,pk=None):
    if request.method=="GET":
        if pk is not None:
            return error("Méthode non autorisée.",405)
        qs=company.departures.select_related("route","bus").order_by("-starts_at","-id")
        # Apply filters before pagination, always scoped to the owner.
        status = request.GET.get("status", "")
        route_id = request.GET.get("route_id", "")
        date_from = request.GET.get("date_from", "")
        date_to = request.GET.get("date_to", "")
        if status:
            if status not in D.values:
                return error("Statut invalide.")
            qs = qs.filter(status=status)
        if route_id:
            try:
                route_id = int(route_id)
            except ValueError:
                return error("Trajet invalide.")
            if not 1 <= route_id <= 2**63-1:
                return error("Trajet invalide.")
            qs = qs.filter(route_id=route_id)
        first = date.fromisoformat(date_from) if date_from else None
        last = date.fromisoformat(date_to) if date_to else None
        if first and last and first > last:
            return error("La date de fin doit suivre la date de début.")
        if first:
            qs = qs.filter(starts_at__gte=datetime.combine(first,time.min,TZ))
        if last:
            qs = qs.filter(starts_at__lt=datetime.combine(last+timedelta(days=1),time.min,TZ))
        # Bounded page, including historical departures.
        try:
            page=int(request.GET.get("page","1"))
        except ValueError:
            page=0
        if not 1<=page<=100000:
            return error("Page invalide.")
        start=(page-1)*50
        rows=list(qs[start:start+51])
        return JsonResponse({"items":[departure_json(d) for d in rows[:50]],"page":page,"has_next":len(rows)>50})
    v=data(request)
    existing=company.departures.filter(pk=pk).first() if pk is not None else None
    if pk is not None and existing is None:
        return error("Départ introuvable.",404)
    if existing and (existing.status!=D.DRAFT or existing.starts_at<=timezone.now()):
        return error("Seuls les brouillons futurs sont modifiables.",409)
    if existing and v.get("frequency","once")!="once":
        raise ValueError("Un départ existant se modifie individuellement.")
    bus=company.buses.filter(pk=integer(v,"bus_id",1,2**63-1),active=True).first()
    route=company.routes.filter(pk=integer(v,"route_id",1,2**63-1),active=True).first()
    if not bus or not route:
        return error("Car ou trajet introuvable ou inactif.",404)
    capacity=integer(v,"capacity",1,bus.capacity)
    price=integer(v,"price",1,1000000)
    premium=integer({"premium_capacity":v.get("premium_capacity",existing.premium_capacity if existing else 0)},"premium_capacity",0,min(capacity-1,bus.premium_capacity))
    if capacity-premium>bus.capacity-bus.premium_capacity:
        raise ValueError("Trop de places Standard pour ce car.")
    premium_price=integer({"premium_price":v.get("premium_price",existing.premium_price if existing else 0)},"premium_price",price if premium else 0,1000000 if premium else 0)
    starts=plan_dates(v)
    duration=timedelta(minutes=route.duration_minutes)
    if any(b<a+duration for a,b in zip(starts,starts[1:])):
        return error("Les départs de cette série se chevauchent.",409)
    occupied=bus.departures.exclude(status=D.CANCELLED)
    if existing:
        occupied=occupied.exclude(pk=existing.pk)
    for s in starts:
        if occupied.filter(starts_at__lt=s+duration,ends_at__gt=s).exists():
            return error("Ce car est déjà affecté sur cette période. Aucun départ créé ou modifié.",409)
    if existing:
        existing.bus,existing.route,existing.starts_at,existing.ends_at,existing.price,existing.capacity=bus,route,starts[0],starts[0]+duration,price,capacity
        existing.premium_capacity,existing.premium_price=premium,premium_price
        existing.save()
        return JsonResponse({"items":[departure_json(existing)]})
    rows=[Departure(company=company,bus=bus,route=route,starts_at=s,ends_at=s+duration,price=price,capacity=capacity,premium_capacity=premium,premium_price=premium_price) for s in starts]
    Departure.objects.bulk_create(rows)
    return JsonResponse({"items":[departure_json(d) for d in rows]},status=201)

@company_endpoint
def departure_status(request,company,pk):
    if request.method!="POST":
        return error("Méthode non autorisée.",405)
    d=company.departures.select_related("bus","route").filter(pk=pk).first()
    if not d:
        return error("Départ introuvable.",404)
    target=data(request).get("status")
    allowed={D.DRAFT:(D.PUBLISHED,D.CANCELLED),D.PUBLISHED:(D.SUSPENDED,D.CANCELLED),D.SUSPENDED:(D.PUBLISHED,D.CANCELLED),D.CANCELLED:()}
    if d.starts_at<=timezone.now() or target not in allowed[d.status]:
        return error("Ce changement de statut n’est pas autorisé.",409)
    if target==D.PUBLISHED and (company.status!=Company.Status.VERIFIED or not d.bus.active or not d.route.active or d.capacity>d.bus.capacity or d.premium_capacity>d.bus.premium_capacity or d.capacity-d.premium_capacity>d.bus.capacity-d.bus.premium_capacity):
        return error("La compagnie, le car et le trajet doivent être actifs et validés.",403)
    if target==D.CANCELLED and active_legs(timezone.now()).filter(departure=d).exists():
        return error("Des réservations sont en attente. Attendez leur expiration avant d’annuler le départ.",409)
    d.status=target
    d.save(update_fields=["status"])
    return JsonResponse(departure_json(d))

@company_endpoint
def publish_batch(request,company):
    if request.method != "POST":
        return error("Méthode non autorisée.",405)
    if company.status != Company.Status.VERIFIED:
        return error("Votre compagnie doit être validée.",403)
    ids = data(request).get("ids")
    if not isinstance(ids,list) or not 1 <= len(ids) <= 50 or any(type(i) is not int or not 1 <= i <= 2**63-1 for i in ids):
        return error("Sélectionnez entre 1 et 50 départs.")
    if len(set(ids)) != len(ids):
        return error("Sélection invalide.")
    rows = list(company.departures.select_related("bus","route").filter(pk__in=ids))
    if len(rows) != len(ids):
        return error("Un départ sélectionné est introuvable.",404)
    now = timezone.now()
    if any(d.status != D.DRAFT or d.starts_at <= now for d in rows):
        return error("Seuls les brouillons futurs peuvent être publiés ensemble. Aucun départ publié.",409)
    if any(not d.bus.active or not d.route.active or d.capacity > d.bus.capacity or d.premium_capacity>d.bus.premium_capacity or d.capacity-d.premium_capacity>d.bus.capacity-d.bus.premium_capacity or d.bus.company_id != company.id or d.route.company_id != company.id for d in rows):
        return error("Un car ou trajet sélectionné est invalide ou inactif. Aucun départ publié.",409)
    # company_endpoint holds the company row lock throughout validation and update.
    count = company.departures.filter(pk__in=ids).update(status=D.PUBLISHED)
    return JsonResponse({"published":count})

@company_endpoint
def reservations(request,company):
    if request.method!="GET":
        return error("Méthode non autorisée.",405)
    from .models import BookingLeg, Booking
    now=timezone.now()
    rows=BookingLeg.objects.filter(departure__company=company).select_related("booking","departure__route").order_by("-id")[:100]
    return JsonResponse({"items":[{"id":l.id,"reference":str(l.booking.request_id),"origin":l.departure.route.origin,"destination":l.departure.route.destination,"starts_at":l.departure.starts_at.isoformat(),"count":l.booking.passengers,"total":l.total,"premium_count":l.premium_count,"status":"EXPIRED" if l.booking.status==Booking.Status.HELD and l.booking.expires_at<=now else l.booking.status,"expires_at":l.booking.expires_at.isoformat()} for l in rows]})
