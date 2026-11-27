from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_GET,require_POST
from .models import Notification,CompanyAgent,Company,User,PushSubscription,PushDelivery
from django.db import transaction
import os
from .views import error

@transaction.atomic
def notify(recipient_id,kind,title,message):
    notice = Notification.objects.create(recipient_id=recipient_id,kind=kind,title=title,message=message[:500])
    if os.environ.get("SIRAGO_PUSH_ENABLED") == "1":
        PushDelivery.objects.bulk_create([
            PushDelivery(subscription_id=pk, notification=notice, next_attempt=timezone.now())
            for pk in PushSubscription.objects.filter(recipient_id=recipient_id).values_list("pk",flat=True)
        ])
    return notice

def notify_admins(kind,title,message):
    for pk in User.objects.filter(is_active=True,is_superuser=True).values_list("pk",flat=True):
        notify(pk,kind,title,message)

def accessible(request):
    if not request.user.is_authenticated:return None,error("Connexion requise.",401)
    if not request.user.is_active:return None,error("Accès indisponible.",403)
    if CompanyAgent.objects.filter(user=request.user).exclude(company__status=Company.Status.VERIFIED).exists():
        return None,error("Compagnie indisponible.",403)
    return Notification.objects.filter(recipient=request.user),None

@never_cache
@require_GET
def notifications(request):
    qs,denied=accessible(request)
    if denied is not None:return denied
    try:
        page=int(request.GET.get("page","1"))
        if not 1<=page<=100000:raise ValueError
        unread=request.GET.get("unread","0")
        if unread not in ("0","1"):raise ValueError
    except ValueError:return error("Filtre ou page invalide.")
    unread_count=qs.filter(read_at__isnull=True).count()
    if unread=="1":qs=qs.filter(read_at__isnull=True)
    total=qs.count();size=10;offset=(page-1)*size
    rows=qs.order_by("-id")[offset:offset+size]
    return JsonResponse({"items":[{"id":n.id,"kind":n.kind,"title":n.title,"message":n.message,"created_at":n.created_at.isoformat(),"read_at":n.read_at.isoformat() if n.read_at else None} for n in rows],"page":page,"page_size":size,"total":total,"unread_count":unread_count,"has_next":offset+size<total})

@never_cache
@require_GET
def notification_count(request):
    qs,denied=accessible(request)
    return denied if denied is not None else JsonResponse({"unread_count":qs.filter(read_at__isnull=True).count()})

@never_cache
@csrf_protect
@require_POST
def mark_read(request,pk):
    qs,denied=accessible(request)
    if denied is not None:return denied
    if not 1<=pk<=2**63-1 or not qs.filter(pk=pk).exists():return error("Notification introuvable.",404)
    qs.filter(pk=pk,read_at__isnull=True).update(read_at=timezone.now())
    return JsonResponse({"unread_count":qs.filter(read_at__isnull=True).count()})

@never_cache
@csrf_protect
@require_POST
def mark_all_read(request):
    qs,denied=accessible(request)
    if denied is not None:return denied
    qs.filter(read_at__isnull=True).update(read_at=timezone.now())
    return JsonResponse({"unread_count":qs.filter(read_at__isnull=True).count()})
