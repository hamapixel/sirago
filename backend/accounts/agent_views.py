import uuid
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import IntegrityError,transaction
from django.http import JsonResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods,require_POST
from .models import Company,CompanyAgent,User
from .views import data,error,field,phone_number

def owner_company(request):
    if not request.user.is_authenticated:return None,error("Connexion requise.",401)
    if request.user.is_superuser or request.user.role!=User.Role.COMPANY or CompanyAgent.objects.filter(user=request.user).exists():
        return None,error("Accès réservé au responsable.",403)
    company=Company.objects.select_for_update().filter(owner=request.user,status=Company.Status.VERIFIED).first()
    return (company,None) if company else (None,error("Compagnie vérifiée requise.",403))

def row(a):
    u=a.user
    return {"id":a.pk,"first_name":u.first_name,"last_name":u.last_name,"phone":u.phone,"email":u.email,"role":a.role,"active":u.is_active}

def set_password(user,values):
    password=values.get("password")
    if not isinstance(password,str) or not 8<=len(password)<=128 or password!=values.get("password_confirmation"):
        raise ValueError("Mot de passe invalide ou confirmation différente (8 à 128 caractères).")
    validate_password(password,user=user)
    user.set_password(password)

@never_cache
@csrf_protect
@require_http_methods(["GET","POST"])
def agents(request):
    try:
        with transaction.atomic():
            c,denied=owner_company(request)
            if denied is not None:return denied
            if request.method=="GET":
                return JsonResponse({"items":[row(a) for a in c.agents.select_related("user").order_by("id")]})
            if c.agents.count()>=100:return error("Limite de 100 comptes agents atteinte.",409)
            v=data(request)
            role=v.get("role")
            if role not in CompanyAgent.Role.values:raise ValueError("Rôle invalide.")
            email=field(v,"email",254,False).lower()
            if email:validate_email(email)
            u=User(username=uuid.uuid4().hex,role=User.Role.COMPANY,first_name=field(v,"first_name",150),last_name=field(v,"last_name",150),phone=phone_number(field(v,"phone",30)),email=email)
            set_password(u,v)
            u.save()
            a=CompanyAgent.objects.create(user=u,company=c,role=role)
            return JsonResponse(row(a),status=201)
    except ValidationError as exc:return error(" ".join(exc.messages))
    except ValueError as exc:return error(str(exc))
    except IntegrityError:return error("Téléphone ou email déjà utilisé.",409)

@never_cache
@csrf_protect
@require_POST
def agent_update(request,pk):
    try:
        with transaction.atomic():
            c,denied=owner_company(request)
            if denied is not None:return denied
            if not 1<=pk<=2**63-1:return error("Agent introuvable.",404)
            a=c.agents.select_for_update().filter(pk=pk).first()
            if not a:return error("Agent introuvable.",404)
            u=User.objects.select_for_update().get(pk=a.user_id)
            v=data(request)
            action=v.get("action")
            if action=="disable":
                u.is_active=False
                u.set_unusable_password()
                u.save(update_fields=["is_active","password"])
            elif action in ("enable","reset_password"):
                if action=="reset_password" and not u.is_active:return error("Réactivez cet agent.",409)
                set_password(u,v)
                u.is_active=True
                u.save(update_fields=["is_active","password"])
            elif action=="role":
                role=v.get("role")
                if role not in CompanyAgent.Role.values:raise ValueError("Rôle invalide.")
                a.role=role;a.save(update_fields=["role"])
            else:raise ValueError("Action invalide.")
            a.user=u
            return JsonResponse(row(a))
    except ValidationError as exc:return error(" ".join(exc.messages))
    except ValueError as exc:return error(str(exc))
