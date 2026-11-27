"""Password-first, server-side TOTP challenge for superusers only."""
import base64
import hashlib
import hmac
import secrets
import time
from io import BytesIO

import pyotp
import qrcode
from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from django.contrib.auth import login, logout
from django.core.cache import cache
from django.db import transaction
from django.http import JsonResponse
from django.middleware.csrf import rotate_token
from django.utils import timezone
from django.utils.crypto import salted_hmac
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST
from .models import AdminMFA, AdminMFAEvent, User
from .views import data, error, profile

PENDING = "admin_mfa_pending"
VERIFIED = "admin_mfa_verified"
TTL = 300


def digest(value):
    return hashlib.sha256(value.encode("ascii")).hexdigest()


def cipher():
    # Domain-separated encryption key; preserve the Django secret with backups.
    key = salted_hmac("sirago.admin.mfa.encryption.v1", "fernet", secret=settings.SECRET_KEY,
                      algorithm="sha256").digest()
    return Fernet(base64.urlsafe_b64encode(key))


def event(user, kind):
    AdminMFAEvent.objects.create(user=user, kind=kind)


def begin(request, user):
    # No authenticated session exists before the second factor.
    logout(request)
    state = AdminMFA.objects.filter(user=user).first()
    request.session[PENDING] = {
        "uid": user.pk, "password_hash": user.get_session_auth_hash(),
        "expires": int(time.time()) + TTL,
        "version": str(state.version) if state else "",
    }
    rotate_token(request)
    event(user, "PASSWORD_ACCEPTED")
    return JsonResponse({"mfa_required": True, "stage": "verify" if state and state.enabled else "enroll"})


def pending(request):
    p = request.session.get(PENDING)
    if not settings.SIRAGO_ADMIN_MFA_REQUIRED or request.user.is_authenticated or not isinstance(p, dict):
        return None, None
    if p.get("expires", 0) <= time.time():
        request.session.pop(PENDING, None)
        return None, None
    user = User.objects.filter(pk=p.get("uid"), is_active=True, is_superuser=True).first()
    if not user or not hmac.compare_digest(p.get("password_hash", ""), user.get_session_auth_hash()):
        request.session.pop(PENDING, None)
        return None, None
    return p, user


def throttled(user):
    # Shared Redis in production, account scoped rather than source-IP scoped.
    key = "admin-mfa-attempts:" + str(user.pk)
    if cache.add(key, 1, 300):
        return False
    try:
        return cache.incr(key) > 8
    except ValueError:
        # An expired counter cannot authorize a verification.
        return True


def locked_user(user, p):
    current = User.objects.select_for_update().filter(pk=user.pk, is_active=True, is_superuser=True).first()
    if current and hmac.compare_digest(p["password_hash"], current.get_session_auth_hash()):
        return current
    return None


def counter_for(secret, code, last):
    if not isinstance(code, str) or len(code) != 6 or not code.isascii() or not code.isdigit():
        return None
    otp = pyotp.TOTP(secret)
    step = int(time.time()) // 30
    # Accept one adjacent step for clock skew; monotonically consume each step.
    for candidate in (step, step - 1, step + 1):
        if candidate > last and hmac.compare_digest(otp.generate_otp(candidate), code):
            return candidate
    return None


def new_recovery():
    codes = [secrets.token_hex(16).upper() for _ in range(8)]
    return codes, [digest(code) for code in codes]


def finish(request, user, state, codes=None):
    request.session.pop(PENDING, None)
    login(request, user, backend="django.contrib.auth.backends.ModelBackend")
    request.session[VERIFIED] = str(state.version)
    result = {"account": profile(user)}
    if codes is not None:
        result["recovery_codes"] = codes
    return JsonResponse(result)


def reject(user, message="Code incorrect ou expiré.", status=400):
    event(user, "VERIFICATION_FAILED")
    return error(message, status)


@never_cache
@csrf_protect
@require_POST
def enroll(request):
    p, user = pending(request)
    if user is None:
        return error("Recommencez la connexion.", 401)
    if throttled(user):
        return reject(user, "Trop de tentatives. Réessayez dans quelques minutes.", 429)
    try:
        token = data(request).get("activation_code")
    except ValueError:
        return reject(user)
    if not isinstance(token, str) or not token.isascii() or len(token) != 48:
        return reject(user)
    with transaction.atomic():
        user = locked_user(user, p)
        if user is None:
            return error("Recommencez la connexion.", 401)
        state = AdminMFA.objects.select_for_update().filter(user=user).first()
        if (not state or state.enabled or not state.enrollment_expires
                or state.enrollment_expires <= timezone.now()
                or not hmac.compare_digest(state.enrollment_hash, digest(token))):
            return reject(user)
        secret = pyotp.random_base32()
        p.update({"secret": cipher().encrypt(secret.encode("ascii")).decode("ascii"),
                  "version": str(state.version), "enrollment_hash": state.enrollment_hash})
        request.session[PENDING] = p
        uri = pyotp.TOTP(secret).provisioning_uri(name=user.username, issuer_name="SiraGo")
        out = BytesIO()
        qrcode.make(uri).save(out, format="PNG")
        event(user, "ENROLLMENT_STARTED")
        return JsonResponse({"secret": secret, "qr": "data:image/png;base64," + base64.b64encode(out.getvalue()).decode("ascii")})


@never_cache
@csrf_protect
@require_POST
def verify(request):
    p, user = pending(request)
    if user is None:
        return error("Recommencez la connexion.", 401)
    if throttled(user):
        return reject(user, "Trop de tentatives. Réessayez dans quelques minutes.", 429)
    try:
        code = data(request).get("code")
    except ValueError:
        return reject(user)
    if not isinstance(code, str) or not code.isascii() or len(code) > 64:
        return reject(user)
    code = code.strip()
    with transaction.atomic():
        user = locked_user(user, p)
        if user is None:
            return error("Recommencez la connexion.", 401)
        state = AdminMFA.objects.select_for_update().filter(user=user).first()
        if not state or str(state.version) != p.get("version"):
            return reject(user, "Recommencez la connexion.", 401)
        if not state.enabled:
            if (not p.get("secret") or not state.enrollment_expires
                    or state.enrollment_expires <= timezone.now()
                    or not hmac.compare_digest(state.enrollment_hash, p.get("enrollment_hash", ""))):
                return reject(user)
            try:
                secret = cipher().decrypt(p["secret"].encode("ascii")).decode("ascii")
            except InvalidToken:
                return reject(user)
            step = counter_for(secret, code, -1)
            if step is None:
                return reject(user)
            codes, state.recovery_hashes = new_recovery()
            state.encrypted_secret = p["secret"]
            state.last_step = step
            state.enabled = True
            state.enrollment_hash = ""
            state.enrollment_expires = None
            state.save()
            event(user, "ENROLLMENT_CONFIRMED")
            return finish(request, user, state, codes)
        try:
            secret = cipher().decrypt(state.encrypted_secret.encode("ascii")).decode("ascii")
        except InvalidToken:
            return reject(user, "Authentification indisponible. Contactez l’administrateur système.", 503)
        step = counter_for(secret, code, state.last_step)
        if step is not None:
            state.last_step = step
            state.save(update_fields=["last_step"])
            event(user, "TOTP_ACCEPTED")
        else:
            normalized = code.upper()
            hashed = digest(normalized)
            matched = next((x for x in state.recovery_hashes if hmac.compare_digest(x, hashed)), None)
            if matched is None:
                return reject(user)
            state.recovery_hashes = [x for x in state.recovery_hashes if x != matched]
            state.save(update_fields=["recovery_hashes"])
            event(user, "RECOVERY_ACCEPTED")
        return finish(request, user, state)


class AdminMFAMiddleware:
    """Fail closed for every authenticated superuser, not just supervision URLs."""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if settings.SIRAGO_ADMIN_MFA_REQUIRED:
            # Native admin's password-only form must not be an alternate login path.
            if request.path_info == "/admin" or request.path_info.startswith("/admin/"):
                return JsonResponse({"detail": "Introuvable."}, status=404)
            if request.user.is_authenticated and request.user.is_superuser:
                version = request.session.get(VERIFIED)
                valid = bool(version) and AdminMFA.objects.filter(
                    user=request.user, enabled=True, version=version).exists()
                if not valid:
                    logout(request)
                    response = error("Double authentification requise. Reconnectez-vous.", 401)
                    response["Cache-Control"] = "no-store"
                    return response
        return self.get_response(request)
