from accounts.notifications import notify
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
from .models import Booking, BookingLeg, Departure, SimulatedPayment
from django.conf import settings
from .ticket_refs import register_refs
from .saspay import sandbox_enabled
from .public_views import public_departures, public_row, bounded_int, minimum_total

def selection(values):
    if any(type(values.get(k)) not in (str,int) for k in ("out","count") if k in values) or ("ret" in values and type(values["ret"]) not in (str,int)):
        raise ValueError("Sélection invalide.")
    out=bounded_int(values.get("out", ""),1,2**63-1)
    ret=bounded_int(values["ret"],1,2**63-1) if values.get("ret") else None
    count=bounded_int(values.get("count","1"),1,100)
    if out==ret:
        raise ValueError("Départs distincts requis.")
    return [out]+([ret] if ret else []),count

def passenger_names(raw,count):
    if not isinstance(raw,list) or len(raw)!=count:
        raise ValueError("Renseignez le nom de chaque passager.")
    names=[]
    for value in raw:
        if not isinstance(value,str) or len(value)>300 or any(ord(ch)<32 and ch!="\t" for ch in value):
            raise ValueError("Nom de passager invalide.")
        name=" ".join(value.split())
        if not 2<=len(name)<=100 or not any(ch.isalpha() for ch in name):
            raise ValueError("Chaque nom doit contenir de 2 à 100 caractères.")
        names.append(name)
    return names

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

def premium_selection(raw,count,legs):
    if raw is None:
        return [[] for _ in range(legs)]
    if not isinstance(raw,list) or len(raw)!=legs:
        raise ValueError("Catégories de places invalides.")
    for positions in raw:
        if not isinstance(positions,list) or len(positions)>count or any(type(i) is not int or not 0<=i<count for i in positions) or len(set(positions))!=len(positions):
            raise ValueError("Catégories de places invalides.")
    return [sorted(p) for p in raw]

def quote_json(rows,count):
    return {"trips":[public_row(d) for d in rows],"count":count,"total":sum(minimum_total(d,count) for d in rows)}

@never_cache
@require_GET
def quote(request):
    try:
        ids,count=selection(request.GET)
        return JsonResponse(quote_json(selected_rows(ids,count,timezone.now()),count))
    except (ValueError,TypeError,OverflowError):
        return error("Ce voyage n’est plus disponible ou la sélection est invalide.",409)

def simulation_enabled():
    return settings.DEBUG and settings.SIRAGO_ENABLE_SIMULATED_PAYMENTS

def booking_json(b):
    now=timezone.now()
    legs=b.history_legs if hasattr(b,"history_legs") else list(b.legs.select_related("departure__route","departure__company","departure__bus").order_by("position"))
    return {"id":b.id,"reference":str(b.request_id),"count":b.passengers,"status":"EXPIRED" if b.status==Booking.Status.HELD and b.expires_at<=now else b.status,"expires_at":b.expires_at.isoformat(),"created_at":b.created_at.isoformat(),
            "passenger_names":b.passenger_names,"ticket_mode":b.ticket_mode,"replacement_id":b.outgoing_report.replacement_id if b.status==Booking.Status.REPORTED and hasattr(b,"outgoing_report") else None,"retained_id":b.outgoing_report.retained_id if b.status==Booking.Status.REPORTED and hasattr(b,"outgoing_report") else None,"total":sum(l.total for l in legs),
            "simulation_enabled":simulation_enabled(),
            "sandbox_checkout_enabled":sandbox_enabled(),
            "sandbox_checkout":({"status":b.sandbox_checkout.status,"amount":b.sandbox_checkout.amount,"checkout_url":b.sandbox_checkout.checkout_url if b.sandbox_checkout.status=="PENDING" and b.status==Booking.Status.HELD and b.expires_at>now and sandbox_enabled() else ""} if hasattr(b,"sandbox_checkout") else None),
            "simulated_payment":({"amount":b.simulated_payment.amount,"network":b.simulated_payment.network,"created_at":b.simulated_payment.created_at.isoformat()} if b.status==Booking.Status.TEST_PAID and hasattr(b,"simulated_payment") else None),
            "trips":[{"id":l.departure_id,"company":l.departure.company.name,"origin":l.departure.route.origin,"destination":l.departure.route.destination,"starts_at":l.departure.starts_at.isoformat(),"ends_at":l.departure.ends_at.isoformat(),"boarding_point":l.departure.route.boarding_point,"arrival_point":l.departure.route.arrival_point,"bus_name":l.departure.bus.name,"price":l.unit_price,"premium_price":l.premium_unit_price,"premium_positions":l.premium_positions,"total":l.total} for l in legs]}

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
        v=data(request, max_bytes=65536)
        mode=v.get("ticket_mode","group")
        if mode not in ("group","individual"):
            raise ValueError("Format de billet invalide.")
        ids,count=selection(v)
        names=passenger_names(v.get("passenger_names"),count)
        classes=premium_selection(v.get("premium_positions"),count,len(ids))
        key=UUID(str(v.get("request_id","")))
        expected=v.get("total")
        if type(expected) is not int or expected<1:
            raise ValueError("Total invalide.")
        with transaction.atomic():
            # Serialize retries per traveler and writes with company management.
            User.objects.select_for_update().get(pk=request.user.pk)
            old=Booking.objects.filter(traveler=request.user,request_id=key).first()
            if old:
                if list(old.legs.order_by("position").values_list("departure_id",flat=True))!=ids or old.passengers!=count or old.ticket_mode!=mode or old.passenger_names!=names or [l.premium_positions for l in old.legs.order_by("position")]!=classes or sum(l.total for l in old.legs.all())!=expected:
                    return error("Référence de requête déjà utilisée.",409)
                return JsonResponse(booking_json(old))
            company_ids=list(Departure.objects.filter(pk__in=ids).values_list("company_id",flat=True).distinct())
            list(Company.objects.select_for_update().filter(pk__in=company_ids).order_by("pk"))
            now=timezone.now()
            rows=selected_rows(ids,count,now)
            if any(len(p)>d.premium_remaining or count-len(p)>d.standard_remaining for d,p in zip(rows,classes)):
                return error("Places insuffisantes dans cette catégorie. Modifiez votre choix.",409)
            total=sum((count-len(p))*d.price+len(p)*d.premium_price for d,p in zip(rows,classes))
            if total!=expected:
                return error("Le tarif a changé. Actualisez le récapitulatif.",409)
            if Booking.objects.filter(traveler=request.user,status=Booking.Status.HELD,expires_at__gt=now).count()>=3:
                return error("Vous avez déjà trois réservations en attente. Annulez-en une ou attendez son expiration.",409)
            expiry=min(now+timedelta(minutes=15),*(d.starts_at for d in rows))
            b=Booking.objects.create(traveler=request.user,request_id=key,passengers=count,passenger_names=names,ticket_mode=mode,expires_at=expiry)
            BookingLeg.objects.bulk_create([BookingLeg(booking=b,departure=d,position=i,unit_price=d.price,premium_count=len(classes[i]),premium_positions=classes[i],premium_unit_price=d.premium_price if classes[i] else 0) for i,d in enumerate(rows)])
            notify(b.traveler_id,"RESERVATION","Réservation enregistrée",f"{count} place(s) réservée(s) temporairement. Finalisez le paiement avant expiration.")
            return JsonResponse(booking_json(b),status=201)
    except (ValueError,TypeError,OverflowError) as exc:
        return error(str(exc),409)

@never_cache
@require_GET
def mine(request):
    denied=traveler_error(request)
    if denied is not None:return denied
    from .booking_history import history
    try:
        rows,meta=history(request,timezone.now())
    except (ValueError,OverflowError):
        return error("Recherche, statut ou pagination invalide.")
    return JsonResponse({"items":[booking_json(b) for b in rows],**meta})

@never_cache
@require_GET
def detail(request,pk):
    denied=traveler_error(request)
    if denied is not None:return denied
    if not 1<=pk<=2**63-1:
        return error("Réservation introuvable.",404)
    b=Booking.objects.filter(pk=pk,traveler=request.user).first()
    if b is None:return error("Réservation introuvable.",404)
    return JsonResponse(booking_json(b))

@never_cache
@csrf_protect
@require_POST
def cancel(request,pk):
    denied=traveler_error(request)
    if denied is not None:return denied
    with transaction.atomic():
        b=Booking.objects.select_for_update().filter(pk=pk,traveler=request.user).first()
        if not b:return error("Réservation introuvable.",404)
        if hasattr(b,"sandbox_checkout") and b.sandbox_checkout.status not in ("EXPIRED","CANCELLED"):
            return error("Une session SasPay existe. Vérifiez son statut avant toute annulation.",409)
        if b.status==Booking.Status.HELD and b.expires_at>timezone.now():
            b.status=Booking.Status.CANCELLED
            b.save(update_fields=["status"])
            notify(b.traveler_id,"CANCELLED","Réservation annulée","Votre réservation a été annulée et les places libérées.")
        return JsonResponse(booking_json(b))


@never_cache
@csrf_protect
@require_POST
def simulate_payment(request,pk):
    if not simulation_enabled():
        return error("Simulation indisponible.",404)
    denied=traveler_error(request)
    if denied is not None:
        return denied
    if not 1<=pk<=2**63-1:
        return error("Réservation introuvable.",404)
    try:
        network=data(request).get("network")
    except (ValueError, TypeError):
        return error("Données invalides.",400)
    if network not in ("orange_ml","moov_ml"):
        return error("Réseau de test invalide.",400)
    with transaction.atomic():
        # Same lock order as reserve; serialize against cancellation and company changes.
        User.objects.select_for_update().get(pk=request.user.pk)
        b=Booking.objects.select_for_update().filter(pk=pk,traveler=request.user).first()
        if b is None:
            return error("Réservation introuvable.",404)
        if b.status==Booking.Status.TEST_PAID:
            return JsonResponse(booking_json(b))
        if hasattr(b,"sandbox_checkout"):
            return error("Une session SasPay est déjà associée à cette réservation.",409)
        ids=list(b.legs.values_list("departure__company_id",flat=True).distinct())
        list(Company.objects.select_for_update().filter(pk__in=ids).order_by("pk"))
        now=timezone.now()
        if b.status!=Booking.Status.HELD or b.expires_at<=now:
            return error("Réservation expirée ou annulée.",409)
        legs=list(b.legs.select_related("departure__company","departure__bus","departure__route"))
        if not legs or any(l.departure.starts_at<=now or l.departure.status!=Departure.Status.PUBLISHED or l.departure.company.status!=Company.Status.VERIFIED or not l.departure.bus.active or not l.departure.route.active for l in legs):
            return error("Un départ n’est plus disponible.",409)
        amount=sum(l.total for l in legs)
        SimulatedPayment.objects.create(booking=b,amount=amount,network=network)
        b.status=Booking.Status.TEST_PAID
        b.save(update_fields=["status"])
        register_refs(b,legs)
        notify(b.traveler_id,"TEST_PAYMENT","Billets de test disponibles","Paiement simulé réussi. Aucun argent débité. Consultez Mes billets.")
        for l in legs:
            d=l.departure
            notify(d.company.owner_id,"TEST_BOOKING","Nouvelle réservation TEST",f"{d.route.origin} → {d.route.destination} : {b.passengers} passager(s). Aucun encaissement réel.")
        return JsonResponse(booking_json(b))
