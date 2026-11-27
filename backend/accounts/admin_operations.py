"""MFA-protected, narrowly scoped supervision mutations and audit history."""
from functools import wraps
from django.db import transaction
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods, require_GET
from fleet.availability import active_legs
from fleet.listing import page_slice
from .mfa import VERIFIED
from .models import AdminAction, AdminMFA, Company, User, SupportRequest, PushSubscription
from .notifications import notify
from .views import data, error, field

def authorized(fn):
    @wraps(fn)
    def wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return error("Connexion requise.", 401)
        if not request.user.is_active or not request.user.is_superuser:
            return error("Accès réservé au superadministrateur.", 403)
        version = request.session.get(VERIFIED)
        if not version or not AdminMFA.objects.filter(user=request.user, enabled=True, version=version).exists():
            return error("Double authentification requise. Reconnectez-vous.", 403)
        try:
            return fn(request, *args, **kwargs)
        except (ValueError, OverflowError) as exc:
            return error(str(exc))
    return wrapped

def change(request, keys):
    values = data(request)
    if set(values) != set(keys) | {"confirm", "reason"} or values.get("confirm") is not True:
        raise ValueError("Confirmez explicitement l'action et renseignez les champs attendus.")
    reason = field(values, "reason", 300)
    if len(reason) < 5 or any(ord(ch) < 32 for ch in reason):
        raise ValueError("Motif obligatoire de 5 à 300 caractères, sans caractères de contrôle.")
    return values, reason

def audit(request, kind, obj, before, after, reason):
    AdminAction.objects.create(actor=request.user, target_type=kind, target_id=obj.pk,
                               before=before, after=after, reason=reason)

def future_legs():
    now = timezone.now()
    return active_legs(now).filter(departure__starts_at__gt=now)

def company_row(obj):
    return {"id":obj.pk,"name":obj.name,"city":obj.city,"address":obj.address,
            "registration_number":obj.registration_number,"status":obj.status,
            "owner":obj.owner.get_full_name() or obj.owner.username,"created_at":obj.created_at.isoformat()}

def traveler_row(obj):
    return {"id":obj.pk,"name":obj.get_full_name() or obj.username,
            "active":obj.is_active,"created_at":obj.date_joined.isoformat()}

def support_row(obj):
    return {"id":obj.pk,"reference":str(obj),"subject":obj.subject,"category":obj.get_category_display(),
            "message":obj.message,"reply":obj.reply,"status":obj.status,
            "requester":obj.requester.get_full_name() or obj.requester.username,
            "created_at":obj.created_at.isoformat(),"updated_at":obj.updated_at.isoformat()}

@never_cache
@csrf_protect
@require_http_methods(["GET","POST"])
@authorized
def company(request, pk):
    with transaction.atomic():
        qs=Company.objects
        if request.method=="POST":
            qs=qs.select_for_update()
        obj=qs.filter(pk=pk).first()
        if obj is None:return error("Compagnie introuvable.",404)
        if request.method=="GET":return JsonResponse(company_row(obj))
        v,reason=change(request,{"status","expected_status"})
        if v["expected_status"]!=obj.status:return error("La fiche a changé. Actualisez-la.",409)
        target=v["status"]
        allowed={"PENDING":("VERIFIED","REJECTED"),"REJECTED":("PENDING",),
                 "VERIFIED":("SUSPENDED",),"SUSPENDED":("VERIFIED",)}
        if target not in allowed.get(obj.status,()):return error("Transition de statut interdite.",409)
        if target=="VERIFIED" and not obj.owner.is_active:return error("Le responsable est inactif.",409)
        if target=="SUSPENDED" and future_legs().filter(departure__company=obj).exists():
            return error("Des réservations futures sont actives. Traitez-les avant la suspension.",409)
        previous=obj.status
        obj.status=target
        obj.save(update_fields=["status"])
        audit(request,"COMPANY",obj,previous,target,reason)
        notify(obj.owner_id,"COMPANY","Statut de votre compagnie","Votre compagnie : "+obj.get_status_display()+". Consultez votre espace.")
        return JsonResponse(company_row(obj))

@never_cache
@csrf_protect
@require_http_methods(["GET","POST"])
@authorized
def traveler(request, pk):
    with transaction.atomic():
        qs=User.objects.filter(role=User.Role.TRAVELER,is_superuser=False,is_staff=False)
        if request.method=="POST":qs=qs.select_for_update()
        obj=qs.filter(pk=pk).first()
        if obj is None:return error("Voyageur introuvable.",404)
        if request.method=="GET":return JsonResponse(traveler_row(obj))
        v,reason=change(request,{"active","expected_active"})
        if type(v["active"]) is not bool or type(v["expected_active"]) is not bool:
            raise ValueError("Statut invalide.")
        if v["expected_active"]!=obj.is_active or v["active"]==obj.is_active:
            return error("La fiche a changé. Actualisez-la.",409)
        if not v["active"] and future_legs().filter(booking__traveler=obj).exists():
            return error("Ce voyageur a des réservations futures actives. Traitez-les avant la désactivation.",409)
        previous="ACTIVE" if obj.is_active else "INACTIVE"
        obj.is_active=v["active"]
        obj.session_version+=1
        obj.save(update_fields=["is_active","session_version"])
        PushSubscription.objects.filter(recipient=obj).delete()
        audit(request,"TRAVELER",obj,previous,"ACTIVE" if obj.is_active else "INACTIVE",reason)
        return JsonResponse(traveler_row(obj))

@never_cache
@csrf_protect
@require_http_methods(["GET","POST"])
@authorized
def support(request, pk):
    with transaction.atomic():
        qs=SupportRequest.objects
        if request.method=="POST":qs=qs.select_for_update()
        obj=qs.filter(pk=pk).first()
        if obj is None:return error("Demande introuvable.",404)
        if request.method=="GET":return JsonResponse(support_row(obj))
        v,reason=change(request,{"status","reply","expected_updated_at"})
        if v["expected_updated_at"]!=obj.updated_at.isoformat():
            return error("La demande a changé. Actualisez-la.",409)
        target=v["status"]
        reply=field(v,"reply",4000,False)
        if target not in SupportRequest.Status.values:raise ValueError("Statut invalide.")
        if target=="RESOLVED" and not reply:raise ValueError("Une réponse est requise pour résoudre la demande.")
        if target==obj.status and reply==obj.reply:return error("Aucune modification.",409)
        previous=obj.status
        obj.status=target
        obj.reply=reply
        obj.save(update_fields=["status","reply","updated_at"])
        audit(request,"SUPPORT",obj,previous,target,reason)
        notify(obj.requester_id,"SUPPORT","Votre demande d’assistance a été mise à jour",
               f"{obj} · {obj.get_status_display()}. Consultez votre centre d’assistance.")
        return JsonResponse(support_row(obj))

@never_cache
@require_GET
@authorized
def history(request):
    qs=AdminAction.objects.select_related("actor").order_by("-id")
    kind=request.GET.get("kind","")
    if kind:
        if kind not in ("COMPANY","TRAVELER","SUPPORT"):raise ValueError("Type invalide.")
        qs=qs.filter(target_type=kind)
    rows,meta=page_slice(request,qs)
    return JsonResponse({"items":[{"id":a.pk,"actor":a.actor.username,"target_type":a.target_type,
        "target_id":a.target_id,"before":a.before,"after":a.after,"reason":a.reason,
        "created_at":a.created_at.isoformat()} for a in rows],**meta})
