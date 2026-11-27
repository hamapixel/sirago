from accounts.notifications import notify
from datetime import date, datetime, time, timedelta
from functools import wraps
from zoneinfo import ZoneInfo
from django.db import IntegrityError, transaction
from django.db.models import Q, TextField, Exists, OuterRef
from django.db.models.functions import Cast
from .listing import search_term, page_slice
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods
from accounts.models import Company, User, CompanyAgent
from accounts.views import data, field, error, phone_number
from .models import Bus, Route, Departure
from .availability import active_legs, with_remaining

from .localities import valid_localities
CITIES = ["Bamako","Kayes","Koulikoro","Sikasso","Ségou","Mopti","Tombouctou","Gao","Kidal","Taoudenni","Ménaka","Nioro du Sahel","Kita","Dioïla","Nara","Bougouni","Koutiala","San","Douentza","Bandiagara","Bafoulabé","Yélimané","Kéniéba","Ambidédi","Aourou","Diamou","Oussoubidiagna","Ségala","Sadiola","Banamba","Kangaba","Kati","Kolokani","Nyamina","Siby","Néguéla","Kadiolo","Dandéresso","Kignan","Kléla","Lobougoula","Loulouni","Niéna","Bla","Barouéli","Niono","Macina","Dioro","Farako","Nampala","Sokolo","Markala","Sarro","Djenné","Ténenkou","Youwarou","Konna","Korientzé","Sofara","Toguéré-Coumbé","Goundam","Diré","Niafunké","Gourma-Rharous","Bintagoungou","Saraféré","Bambara Maoudé","Léré","Gossi","Tonka","Ber","Gargando","Bourem","Ansongo","Almoustrat","Bamba","Ouattagouna","Soni Aliber","Djebock","Talataye","Tessit","N'Tillit","Gabéro","Ersane","Tabankort","Tin-Aouker","Kassambéré","Abeïbara","Tin-Essako","Tessalit","Achibogho","Anéfif","Timétrine","Aguel-Hoc","Takalote","Araouane","Foum-Elba","Boudje-Béha","Al-Ourche","Achouratt","Tidermène","Inékar","Andéramboukane","Anouzagrène","Diéma","Diangounté","Sandaré","Troungoumbé","Béma","Sagabari","Sébékoro","Toukoto","Séféto","Kolondiéba","Yanfolila","Yorosso","Tominian","Boré","Hombori","N'Gouma","Mondoro","Boni","Koro","Bankass","Kendié","Ningari","Dialassagou","Sangha","Kani","Sokoura","Kalabancoro","Baguinéda","Moribabougou","Mountougoula","Dialakorodji","Sangarébougou","Ouélessébougou","Fana","Massigui","Zantiébougou","Garalo","Sélingué","Koury","Kimparana","Yangasso","Pelengana","Sévaré","Finkolo"]
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
                agent = CompanyAgent.objects.filter(user=request.user).first()
                if agent:
                    company = qs.filter(pk=agent.company_id,status=Company.Status.VERIFIED).first()
                    if not company:return error("Compagnie indisponible.",403)
                    # Recheck under company lock after concurrent disable or role change.
                    agent = CompanyAgent.objects.filter(pk=agent.pk,user__is_active=True).first()
                    if not agent:return error("Agent désactivé.",403)
                    allowed = fn.__module__ == 'fleet.boarding_views' and fn.__name__ in ('lookup','validate','history')
                    allowed = allowed or (request.method=='GET' and fn.__module__=='fleet.manifest_views' and fn.__name__ in ('manifest','manifest_pdf'))
                    allowed = allowed or (request.method=='GET' and fn.__module__=='fleet.views' and (fn.__name__=='departures' or (fn.__name__=='reservations' and agent.role==CompanyAgent.Role.CLERK)))
                    if not allowed:return error("Permission insuffisante.",403)
                    request.company_agent=agent
                else:
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
    locked = getattr(b, "capacity_locked", None)
    if locked is None:
        locked = future_departures(b.departures).exists()
    return {"capacity_locked":locked,"id":b.id,"name":b.name,"plate":b.plate,"capacity":b.capacity,"premium_capacity":b.premium_capacity,"active":b.active,"driver_first_name":b.driver_first_name,"driver_last_name":b.driver_last_name,"driver_phone":b.driver_phone}

def route_json(r):
    return {"id":r.id,"origin":r.origin,"destination":r.destination,"boarding_point":r.boarding_point,"arrival_point":r.arrival_point,"duration_minutes":r.duration_minutes,"price":r.price,"active":r.active}

def departure_json(d):
    result = {"id":d.id,"bus_id":d.bus_id,"bus_name":d.bus.name,"route_id":d.route_id,"origin":d.route.origin,"destination":d.route.destination,"starts_at":d.starts_at.isoformat(),"ends_at":d.ends_at.isoformat(),"capacity":d.capacity,"premium_capacity":d.premium_capacity,"premium_price":d.premium_price,"price":d.price,"status":d.status}
    if hasattr(d,"remaining"):
        result.update(remaining=max(0,d.remaining),standard_remaining=max(0,d.standard_remaining),premium_remaining=max(0,d.premium_remaining))
    return result

def future_departures(qs):
    return qs.exclude(status=D.CANCELLED).filter(ends_at__gt=timezone.now())

@company_endpoint
def overview(request, company):
    if request.method != "GET":
        return error("Méthode non autorisée.",405)
    today = timezone.now().astimezone(TZ).date()
    start = datetime.combine(today,time.min,TZ)
    day = company.departures.filter(starts_at__gte=start, starts_at__lt=start+timedelta(days=1))
    departures = day.filter(status=D.PUBLISHED)
    now = timezone.now()
    capacity = list(with_remaining(departures.filter(starts_at__gt=now), now).values_list("capacity", "remaining"))
    return JsonResponse({"status":company.status,"active_buses":company.buses.filter(active=True).count(),"active_routes":company.routes.filter(active=True).count(),"today_departures":departures.count(),"today_capacity":sum(max(0, remaining) for _, remaining in capacity),"today_total_capacity":sum(total for total, _ in capacity),"today_draft":day.filter(status=D.DRAFT).count(),"today_suspended":day.filter(status=D.SUSPENDED).count(),"today_cancelled":day.filter(status=D.CANCELLED).count()})

@company_endpoint
def buses(request,company,pk=None):
    if request.method == "GET":
        if pk is not None:
            return error("Méthode non autorisée.",405)
        locked_departures = future_departures(company.departures.filter(bus_id=OuterRef("pk")))
        return JsonResponse({"items":[bus_json(b) for b in company.buses.annotate(capacity_locked=Exists(locked_departures)).order_by("name","id")]})
    v=data(request)
    b=company.buses.filter(pk=pk).first() if pk is not None else Bus(company=company)
    if b is None:
        return error("Car introuvable.",404)
    name=field(v,"name",100)
    plate=" ".join(field(v,"plate",40).upper().split())
    capacity=integer(v,"capacity",1,100)
    premium=integer({"premium_capacity":v.get("premium_capacity",b.premium_capacity if pk is not None else 0)},"premium_capacity",0,capacity-1)
    active=flag(v,"active")
    if pk is not None and future_departures(b.departures).exists() and ((b.active and not active) or capacity!=b.capacity or premium!=b.premium_capacity):
        return error("La capacité et la désactivation sont protégées tant que ce car a des départs non terminés. Les autres informations restent modifiables.",409)
    driver = {key: field({key: v.get(key, getattr(b,key))},key,20 if key=="driver_phone" else 100,required=False) for key in ("driver_first_name","driver_last_name","driver_phone")}
    if any(driver.values()):
        if not all(driver.values()):
            raise ValueError("Renseignez le prénom, le nom et le téléphone du chauffeur.")
        driver["driver_phone"]=phone_number(driver["driver_phone"])
    for key,value in driver.items():setattr(b,key,value)
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
    if not valid_localities(origin,destination):
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
        qs=with_remaining(company.departures.select_related("route","bus"),timezone.now()).order_by("-starts_at","-id")
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
        term=search_term(request)
        if term:
            for word in term.split():
                qs=qs.filter(Q(route__origin__icontains=word)|Q(route__destination__icontains=word)|Q(bus__name__icontains=word)|Q(bus__plate__icontains=word)|Q(route__boarding_point__icontains=word))
        rows,meta=page_slice(request,qs,default_size=50)
        return JsonResponse({"items":[departure_json(d) for d in rows],**meta})
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
        return error("Des réservations occupent des places. Impossible d’annuler ce départ.",409)
    previous=d.status
    d.status=target
    d.save(update_fields=["status"])
    if target in (D.SUSPENDED,D.CANCELLED) or (previous==D.SUSPENDED and target==D.PUBLISHED):
        label={D.SUSPENDED:"Départ suspendu",D.CANCELLED:"Départ annulé",D.PUBLISHED:"Départ republié"}[target]
        recipients=active_legs(timezone.now()).filter(departure=d).values_list("booking__traveler_id",flat=True).distinct()
        for recipient in recipients:
            notify(recipient,"DEPARTURE",label,f"{d.route.origin} → {d.route.destination}, {d.starts_at.astimezone(TZ):%d/%m/%Y %H:%M}. Vérifiez les informations de votre réservation.")
    return JsonResponse(departure_json(d))

@company_endpoint
def publish_batch(request,company):
    if request.method != "POST":
        return error("Méthode non autorisée.",405)
    if company.status != Company.Status.VERIFIED:
        return error("Votre compagnie doit être validée.",403)
    payload = data(request)
    ids = payload.get("ids")
    target = payload.get("status", D.PUBLISHED)
    if target not in (D.PUBLISHED,D.SUSPENDED):return error("Statut invalide.")
    if not isinstance(ids,list) or not 1 <= len(ids) <= 50 or any(type(i) is not int or not 1 <= i <= 2**63-1 for i in ids):
        return error("Sélectionnez entre 1 et 50 départs.")
    if len(set(ids)) != len(ids):
        return error("Sélection invalide.")
    rows = list(company.departures.select_related("bus","route").filter(pk__in=ids))
    if len(rows) != len(ids):
        return error("Un départ sélectionné est introuvable.",404)
    now = timezone.now()
    allowed = (D.DRAFT,D.SUSPENDED) if target==D.PUBLISHED else (D.PUBLISHED,)
    if any(d.status not in allowed or d.starts_at <= now for d in rows):
        return error("Sélection de départs futurs invalide. Aucun changement.",409)
    if target==D.PUBLISHED and any(not d.bus.active or not d.route.active or d.capacity > d.bus.capacity or d.premium_capacity>d.bus.premium_capacity or d.capacity-d.premium_capacity>d.bus.capacity-d.bus.premium_capacity or d.bus.company_id != company.id or d.route.company_id != company.id for d in rows):
        return error("Un car ou trajet sélectionné est invalide ou inactif. Aucun départ publié.",409)
    # company_endpoint holds the company row lock throughout validation and update.
    count = company.departures.filter(pk__in=ids).update(status=target)
    for d in rows:
        if target==D.SUSPENDED or d.status==D.SUSPENDED:
            label="Départ suspendu" if target==D.SUSPENDED else "Départ republié"
            for recipient in active_legs(now).filter(departure=d).values_list("booking__traveler_id",flat=True).distinct():
                notify(recipient,"DEPARTURE",label,f"{d.route.origin} → {d.route.destination}, {d.starts_at.astimezone(TZ):%d/%m/%Y %H:%M}.")
    return JsonResponse({"published" if target==D.PUBLISHED else "suspended":count})

@company_endpoint
def reservations(request,company,pk=None):
    if request.method!="GET":
        return error("Méthode non autorisée.",405)
    from .models import BookingLeg, Booking
    if pk is not None:
        from .reservation_detail import reservation_detail
        return reservation_detail(request,company,pk)
    now=timezone.now()
    qs=BookingLeg.objects.filter(departure__company=company).select_related("booking","departure__route").order_by("-id")
    term=search_term(request)
    if term:
        qs=qs.annotate(names_text=Cast("booking__passenger_names",TextField()),ref_text=Cast("booking__request_id",TextField()))
        for word in term.split():
            qs=qs.filter(Q(names_text__icontains=word)|Q(ref_text__icontains=word)|Q(departure__route__origin__icontains=word)|Q(departure__route__destination__icontains=word))
    rows,meta=page_slice(request,qs)
    return JsonResponse({"items":[{"id":l.id,"reference":str(l.booking.request_id),"origin":l.departure.route.origin,"destination":l.departure.route.destination,"starts_at":l.departure.starts_at.isoformat(),"count":l.booking.passengers,**({} if getattr(request,"company_agent",None) else {"total":l.total}),"premium_count":l.premium_count,"status":"EXPIRED" if l.booking.status==Booking.Status.HELD and l.booking.expires_at<=now else l.booking.status,"expires_at":l.booking.expires_at.isoformat()} for l in rows],**meta})
