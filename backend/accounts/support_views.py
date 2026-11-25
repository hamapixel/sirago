from uuid import UUID
from datetime import timedelta
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods
from .models import User,SupportRequest
from .views import data,error,field

def row(t):
    return {"id":t.pk,"reference":str(t),"category":t.category,"subject":t.subject,"message":t.message,
            "status":t.status,"reply":t.reply,"created_at":t.created_at.isoformat(),"updated_at":t.updated_at.isoformat()}

@never_cache
@csrf_protect
@require_http_methods(["GET","POST"])
def requests(request):
    if not request.user.is_authenticated:return error("Connexion requise.",401)
    if request.user.is_superuser or request.user.role not in User.Role.values:return error("Accès indisponible.",403)
    qs=SupportRequest.objects.filter(requester=request.user)
    try:
        if request.method=="GET":
            page=int(request.GET.get("page","1"))
            term=field(request.GET,"q",150,False)
            status=field(request.GET,"status",16,False)
            if not 1<=page<=100000 or (status and status not in SupportRequest.Status.values):raise ValueError("Filtre invalide.")
            if status:qs=qs.filter(status=status)
            if term:
                for word in term.split():
                    if word.upper().startswith("SG-"):
                        fragment=word[3:].lower()
                        from django.db.models.functions import Cast
                        from django.db.models import CharField
                        qs=qs.annotate(ref_text=Cast("reference",CharField())).filter(ref_text__icontains=fragment if len(fragment)<=8 else fragment[:8]+"-"+fragment[8:])
                    else:qs=qs.filter(Q(subject__icontains=word)|Q(message__icontains=word)|Q(reply__icontains=word))
            total=qs.count();offset=(page-1)*10
            return JsonResponse({"items":[row(t) for t in qs.order_by("-id")[offset:offset+10]],"total":total,"page":page,"page_size":10})
        v=data(request)
        reference=UUID(field(v,"request_id",36))
        if reference.version!=4:raise ValueError("Référence invalide.")
        category=field(v,"category",16)
        subject=field(v,"subject",120)
        message=field(v,"message",2000)
        if category not in SupportRequest.Category.values or len(subject)<5 or len(message)<10:raise ValueError("Renseignez une catégorie, un sujet (5 caractères) et un message (10 caractères minimum).")
        with transaction.atomic():
            User.objects.select_for_update().get(pk=request.user.pk)
            previous=qs.filter(reference=reference).first()
            if previous:
                if (previous.category,previous.subject,previous.message)!=(category,subject,message):return error("Cette référence a déjà été utilisée.",409)
                return JsonResponse(row(previous))
            if SupportRequest.objects.filter(reference=reference).exists():return error("Référence indisponible.",409)
            if qs.filter(created_at__gte=timezone.now()-timedelta(hours=1)).count()>=5:return error("Limite de cinq demandes par heure atteinte.",429)
            t=SupportRequest.objects.create(requester=request.user,reference=reference,category=category,subject=subject,message=message)
            return JsonResponse(row(t),status=201)
    except IntegrityError:return error("Référence indisponible. Réessayez avec une nouvelle demande.",409)
    except (ValueError,TypeError,OverflowError) as exc:return error(str(exc))
