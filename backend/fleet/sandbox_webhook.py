"""Authenticated sandbox webhook intake; provider API remains authoritative."""
import hashlib,hmac,json,os,re,time
from uuid import UUID
from django.core.exceptions import RequestDataTooBig
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.views.decorators.cache import never_cache
from .models import SandboxCheckout,SandboxWebhookReceipt
from .saspay import sandbox_tickets_enabled

@csrf_exempt
@never_cache
@require_POST
def receive(request):
    secret=os.getenv("SASPAY_SANDBOX_WEBHOOK_SECRET","")
    if not sandbox_tickets_enabled() or len(secret)<16:return JsonResponse({"detail":"Indisponible."},status=404)
    stamp=request.headers.get("X-Webhook-Timestamp","")
    sig=request.headers.get("X-Webhook-Signature","")
    if not re.fullmatch(r"[0-9]{1,12}",stamp) or abs(time.time()-int(stamp))>300 or not re.fullmatch(r"[0-9a-f]{64}",sig):
        return JsonResponse({"detail":"Signature invalide."},status=403)
    try:
        if int(request.META.get("CONTENT_LENGTH") or 0)>65536:raise ValueError
        body=request.body
        if len(body)>65536:raise ValueError
    except (ValueError,RequestDataTooBig):return JsonResponse({"detail":"Corps invalide."},status=400)
    expected=hmac.new(secret.encode(),stamp.encode()+b"."+body,hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected,sig):return JsonResponse({"detail":"Signature invalide."},status=403)
    try:
        payload=json.loads(body)
        event=payload["event"]
        if event!=request.headers.get("X-Webhook-Event"):raise ValueError
        if event=="webhook.test":return JsonResponse({"accepted":True})
        if event!="transaction.success":return JsonResponse({"accepted":True,"ignored":True})
        data=payload["data"]
        if data["type"]!="PAIEMENT" or data["status"]!="SUCCESS" or data["currency"]!="XOF" or data["country"]!="ML":
            return JsonResponse({"accepted":True,"ignored":True})
        txid=UUID(str(data["id"]))
    except (ValueError,TypeError,KeyError,AttributeError):return JsonResponse({"detail":"Événement invalide."},status=400)
    # No trust in webhook amount or booking association: only retain transaction id.
    receipt,_=SandboxWebhookReceipt.objects.get_or_create(transaction_id=txid)
    if SandboxCheckout.objects.filter(transaction_id=txid).exists() and receipt.matched_at is None:
        SandboxWebhookReceipt.objects.filter(pk=receipt.pk,matched_at__isnull=True).update(matched_at=timezone.now())
    return JsonResponse({"accepted":True},status=202)
