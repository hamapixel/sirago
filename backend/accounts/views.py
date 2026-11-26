import hashlib
import json
import re
import uuid
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.password_validation import validate_password
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import IntegrityError, transaction
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_GET, require_POST
from .models import User, Company, CompanyAgent

def error(message, status=400):
    return JsonResponse({"detail": message}, status=status)

def csrf_failure(request, reason=""):
    return error("Session de sécurité expirée. Actualisez la page et réessayez.", 403)

def data(request, max_bytes=16384):
    if len(request.body) > max_bytes:
        raise ValueError("Requête trop volumineuse.")
    try:
        value = json.loads(request.body)
    except (ValueError, UnicodeDecodeError):
        raise ValueError("Données invalides.")
    if not isinstance(value, dict):
        raise ValueError("Données invalides.")
    return value

def field(values, key, limit, required=True):
    raw = values.get(key, "")
    if not isinstance(raw, str):
        raise ValueError("Champ invalide : " + key)
    value = raw.strip()
    if len(value) > limit or (required and not value):
        raise ValueError("Champ obligatoire ou trop long : " + key)
    return value

def phone_number(raw):
    raw = re.sub(r"[\s-]", "", raw)
    if re.fullmatch(r"[0-9]{8}", raw):
        return "+223" + raw
    if re.fullmatch(r"\+223[0-9]{8}", raw):
        return raw
    raise ValueError("Saisissez un numéro malien de 8 chiffres.")

def limited(request, scope, limit=15):
    ip = request.META.get("REMOTE_ADDR", "unknown")
    key = "auth:" + scope + ":" + hashlib.sha256(ip.encode()).hexdigest()
    if cache.add(key, 1, timeout=600):
        return False
    try:
        return cache.incr(key) > limit
    except ValueError:
        cache.add(key, 1, timeout=600)
        return False

def profile(user):
    result = {"first_name": user.first_name, "last_name": user.last_name, "phone": user.phone,
              "email": user.email, "role": "ADMIN" if user.is_superuser else user.role,
              "company": None}
    if user.is_superuser:
        result["username"] = user.username
    if not user.is_superuser and user.role == User.Role.COMPANY:
        agent = CompanyAgent.objects.select_related("company").filter(user=user).first()
        company = agent.company if agent else Company.objects.filter(owner=user).first()
        if company:
            result["company"] = {"name": company.name, "status": company.status, "city": company.city}
            if company.logo:
                result["company"]["logo"] = company.logo
            if company.banner:
                result["company"]["banner"] = company.banner
            result["company_role"] = agent.role if agent else "OWNER"
    return result

@never_cache
@require_GET
def csrf(request):
    return JsonResponse({"csrfToken": get_token(request)})

def register(request, role):
    if request.user.is_authenticated:
        return error("Déconnectez-vous avant de créer un autre compte.", 409)
    if limited(request, "register", 12):
        return error("Trop de tentatives. Réessayez dans quelques minutes.", 429)
    try:
        values = data(request)
        first = field(values, "first_name", 150)
        last = field(values, "last_name", 150)
        phone = phone_number(field(values, "phone", 30))
        email = field(values, "email", 254, False).lower()
        if email:
            validate_email(email)
        password = values.get("password")
        if not isinstance(password, str) or len(password) > 128 or len(password) < 8:
            raise ValueError("Le mot de passe doit contenir entre 8 et 128 caractères.")
        if password != values.get("password_confirmation"):
            raise ValueError("Les mots de passe ne correspondent pas.")
        if values.get("terms") is not True:
            raise ValueError("Acceptez les conditions d’utilisation.")
        user = User(username=uuid.uuid4().hex, first_name=first, last_name=last, phone=phone, email=email, role=role)
        validate_password(password, user=user)
        company_data = {}
        if role == User.Role.COMPANY:
            company_data = dict(name=field(values, "company_name", 150), city=field(values, "city", 100),
                                address=field(values, "address", 250), registration_number=field(values, "registration_number", 100, False))
        if User.objects.filter(phone=phone).exists() or (email and User.objects.filter(email__iexact=email).exists()):
            return error("Ce téléphone ou cet email est déjà associé à un compte.", 409)
        with transaction.atomic():
            user.set_password(password)
            user.save()
            if role == User.Role.COMPANY:
                Company.objects.create(owner=user, **company_data)
                from .notifications import notify_admins
                notify_admins('COMPANY_REVIEW', 'Nouvelle compagnie à vérifier', 'Une inscription de compagnie attend votre vérification.')
    except ValidationError as exc:
        return error(" ".join(exc.messages))
    except ValueError as exc:
        return error(str(exc))
    except IntegrityError:
        return error("Ce téléphone ou cet email est déjà associé à un compte.", 409)
    login(request, user, backend="django.contrib.auth.backends.ModelBackend")
    return JsonResponse(profile(user), status=201)

@never_cache
@csrf_protect
@require_POST
def register_traveler(request):
    return register(request, User.Role.TRAVELER)

@never_cache
@csrf_protect
@require_POST
def register_company(request):
    return register(request, User.Role.COMPANY)

@never_cache
@csrf_protect
@require_POST
def sign_in(request):
    if limited(request, "login", 20):
        return error("Trop de tentatives. Réessayez dans quelques minutes.", 429)
    try:
        values = data(request)
        identifier = field(values, "identifier", 254)
        password = values.get("password")
        if not isinstance(password, str) or not password or len(password) > 128:
            raise ValueError("Identifiants invalides.")
        if "@" in identifier:
            account = User.objects.filter(email__iexact=identifier).first()
        else:
            try:
                account = User.objects.filter(phone=phone_number(identifier)).first()
            except ValueError:
                account = None
        # Public phone/email identifiers keep priority. Only existing
        # superusers may additionally authenticate with a Django username.
        if account is None:
            account = User.objects.filter(username=identifier, is_superuser=True).first()
        user = authenticate(request, username=account.username if account else "unknown-" + uuid.uuid4().hex, password=password)
        if user is None:
            return error("Identifiants incorrects.", 401)
    except ValueError as exc:
        return error(str(exc))
    agent=CompanyAgent.objects.select_related("company").filter(user=user).first()
    if agent and agent.company.status!=Company.Status.VERIFIED:
        return error("Accès de la compagnie indisponible.",403)
    login(request, user)
    return JsonResponse(profile(user))

@never_cache
@csrf_protect
@require_POST
def sign_out(request):
    if request.user.is_authenticated and request.session.session_key:
        from .models import PushSubscription
        PushSubscription.objects.filter(recipient=request.user, session_key=request.session.session_key).delete()
    logout(request)
    return JsonResponse({"detail": "Déconnecté."})

@never_cache
@require_GET
def me(request):
    if not request.user.is_authenticated:
        return error("Connexion requise.", 401)
    return JsonResponse(profile(request.user))

@never_cache
@require_GET
def company_account(request):
    if not request.user.is_authenticated:
        return error("Connexion requise.", 401)
    if request.user.role != User.Role.COMPANY or request.user.is_superuser:
        return error("Accès réservé aux compagnies.", 403)
    company = Company.objects.filter(owner=request.user).first()
    if not company:
        return error("Compagnie introuvable.", 403)
    return JsonResponse({"name": company.name, "status": company.status, "city": company.city, "address": company.address, "registration_number": company.registration_number, **({"logo": company.logo} if company.logo else {}), **({"banner": company.banner} if company.banner else {})})

def traveler_profile_error(request):
    if not request.user.is_authenticated:
        return error("Connexion requise.", 401)
    if request.user.is_superuser or request.user.role != User.Role.TRAVELER:
        return error("Accès réservé aux voyageurs.", 403)
    return None

@never_cache
@csrf_protect
@require_POST
def update_traveler_profile(request):
    denied = traveler_profile_error(request)
    if denied is not None:
        return denied
    try:
        values = data(request)
        first = " ".join(field(values, "first_name", 150).split())
        last = " ".join(field(values, "last_name", 150).split())
        if not first or not last or any(ord(ch)<32 for ch in first+last):
            raise ValueError("Nom ou prénom invalide.")
    except ValueError as exc:
        return error(str(exc))
    user = request.user
    user.first_name, user.last_name = first, last
    user.save(update_fields=["first_name", "last_name"])
    return JsonResponse(profile(user))

@never_cache
@csrf_protect
@require_POST
def change_traveler_password(request):
    denied = traveler_profile_error(request)
    if denied is not None:
        return denied
    return change_password(request)

def change_password(request):
    if limited(request, "password-change:" + str(request.user.pk), 10):
        return error("Trop de tentatives. Réessayez dans quelques minutes.", 429)
    try:
        values = data(request)
        current = values.get("current_password")
        password = values.get("password")
        if not isinstance(current, str) or not current or len(current)>128:
            raise ValueError("Mot de passe actuel invalide.")
        if not isinstance(password, str) or not 8<=len(password)<=128:
            raise ValueError("Choisissez un mot de passe de 8 à 128 caractères.")
        if password != values.get("password_confirmation"):
            raise ValueError("Les mots de passe ne correspondent pas.")
        with transaction.atomic():
            user = User.objects.select_for_update().get(pk=request.user.pk)
            if not user.check_password(current):
                return error("Mot de passe actuel incorrect.", 400)
            if user.check_password(password):
                return error("Choisissez un nouveau mot de passe.", 400)
            validate_password(password, user=user)
            user.set_password(password)
            user.save(update_fields=["password"])
        update_session_auth_hash(request, user)
    except ValidationError as exc:
        return error(" ".join(exc.messages))
    except ValueError as exc:
        return error(str(exc))
    return JsonResponse({"detail": "Mot de passe modifié."})


def company_profile_error(request):
    if not request.user.is_authenticated:
        return error("Connexion requise.",401)
    if request.user.is_superuser or request.user.role != User.Role.COMPANY or not Company.objects.filter(owner=request.user).exists():
        return error("Accès réservé aux compagnies.",403)
    return None

@never_cache
@csrf_protect
@require_POST
def update_company_profile(request):
    denied=company_profile_error(request)
    if denied is not None:return denied
    try:
        values=data(request)
        first=" ".join(field(values,"first_name",150).split())
        last=" ".join(field(values,"last_name",150).split())
        if not first or not last or any(ord(ch)<32 for ch in first+last):
            raise ValueError("Nom ou prénom invalide.")
    except ValueError as exc:
        return error(str(exc))
    user=request.user
    user.first_name,user.last_name=first,last
    user.save(update_fields=["first_name","last_name"])
    return JsonResponse(profile(user))

@never_cache
@csrf_protect
@require_POST
def change_company_password(request):
    if request.user.is_authenticated and not request.user.is_superuser and request.user.role==User.Role.COMPANY and CompanyAgent.objects.filter(user=request.user,company__status=Company.Status.VERIFIED).exists():
        return change_password(request)
    denied=company_profile_error(request)
    if denied is not None:return denied
    return change_password(request)

def admin_profile_error(request):
    if not request.user.is_authenticated:
        return error("Connexion requise.", 401)
    if not request.user.is_active or not request.user.is_superuser:
        return error("Accès réservé au superadministrateur.", 403)
    return None


@never_cache
@csrf_protect
@require_POST
def update_admin_profile(request):
    denied = admin_profile_error(request)
    if denied is not None:
        return denied
    try:
        values = data(request)
        first = " ".join(field(values, "first_name", 150).split())
        last = " ".join(field(values, "last_name", 150).split())
        if not first or not last or any(ord(ch) < 32 for ch in first + last):
            raise ValueError("Nom ou prénom invalide.")
    except ValueError as exc:
        return error(str(exc))
    user = request.user
    user.first_name, user.last_name = first, last
    user.save(update_fields=["first_name", "last_name"])
    return JsonResponse(profile(user))


@never_cache
@csrf_protect
@require_POST
def change_admin_password(request):
    denied = admin_profile_error(request)
    if denied is not None:
        return denied
    return change_password(request)
