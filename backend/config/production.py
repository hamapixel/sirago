"""Opt-in production settings validation; no network access or secret logging."""
from urllib.parse import urlsplit
import re
from django.core.exceptions import ImproperlyConfigured

LOCAL_HOSTS = ("localhost", "127.0.0.1", "backend")

def production_settings(env):
    def fail(message):
        raise ImproperlyConfigured(message)
    def csv(key):
        return list(dict.fromkeys(v.strip() for v in env.get(key, "").split(",") if v.strip()))
    if env.get("DJANGO_DEBUG") == "1":
        fail("Production: DJANGO_DEBUG doit être désactivé.")
    if env.get("SIRAGO_ENABLE_SIMULATED_PAYMENTS") == "1":
        fail("Production: les paiements simulés doivent être désactivés.")
    secret=env.get("DJANGO_SECRET_KEY","")
    if len(secret)<50 or len(set(secret))<5 or secret.startswith(("django-insecure-","local-dev-")):
        fail("Production: configurez une clé Django secrète et aléatoire.")
    password=env.get("POSTGRES_PASSWORD","")
    if len(password)<16 or password=="local_dev_only_change_me":
        fail("Production: configurez un mot de passe PostgreSQL distinct et robuste.")
    hosts=csv("DJANGO_ALLOWED_HOSTS")
    if not hosts or any(not re.fullmatch(r"(?=.{1,253}$)(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.)+[A-Za-z]{2,63}",h) for h in hosts):
        fail("Production: DJANGO_ALLOWED_HOSTS doit contenir les domaines publics explicites, sans wildcard.")
    origins=csv("DJANGO_CSRF_TRUSTED_ORIGINS")
    if not origins:
        fail("Production: configurez les origines HTTPS de confiance.")
    for origin in origins:
        try:
            u=urlsplit(origin)
            valid=u.scheme=="https" and u.netloc==u.hostname and u.hostname in [h.lower() for h in hosts] and not any((u.path,u.query,u.fragment)) and not u.username
        except ValueError:
            valid=False
        if not valid:
            fail("Production: origine CSRF invalide ou non autorisée.")
    for flag in ("SIRAGO_ENABLE_SASPAY_SANDBOX", "SIRAGO_ENABLE_SASPAY_TICKETS",
                 "SIRAGO_SASPAY_LOCAL_RETURN"):
        if env.get(flag) == "1":
            fail("Production: les options SasPay de test doivent être désactivées.")
    # A local-memory cache would reset counters across workers and restarts.
    redis_url = env.get("SIRAGO_REDIS_URL", "")
    try:
        u = urlsplit(redis_url)
        valid_redis = (
            bool(redis_url) and not any(ch.isspace() for ch in redis_url)
            and u.scheme in ("redis", "rediss") and bool(u.hostname)
            and (u.port is None or 1 <= u.port <= 65535)
            and (not u.path or re.fullmatch(r"/[0-9]+", u.path) is not None)
            and not u.query and not u.fragment
        )
    except ValueError:
        valid_redis = False
    if not valid_redis:
        # Never include the URL: it may contain credentials.
        fail("Production: configurez SIRAGO_REDIS_URL avec une URL Redis valide.")
    # Proxy trust is deliberately explicit: the edge must strip client-supplied headers.
    trust=env.get("DJANGO_TRUST_HTTPS_PROXY")=="1"
    return {
        "SIRAGO_ADMIN_MFA_REQUIRED":True,
        "DEBUG":False,"ALLOWED_HOSTS":hosts+list(LOCAL_HOSTS),
        "CSRF_TRUSTED_ORIGINS":origins,
        "SESSION_COOKIE_SECURE":True,"CSRF_COOKIE_SECURE":True,
        "SECURE_SSL_REDIRECT":True,
        "SECURE_PROXY_SSL_HEADER":("HTTP_X_FORWARDED_PROTO","https") if trust else None,
        "SECURE_HSTS_SECONDS":3600,
        "SECURE_HSTS_INCLUDE_SUBDOMAINS":False,"SECURE_HSTS_PRELOAD":False,
        "SECURE_CONTENT_TYPE_NOSNIFF":True,"SECURE_REFERRER_POLICY":"same-origin",
        "X_FRAME_OPTIONS":"DENY","SIRAGO_ENABLE_SIMULATED_PAYMENTS":False,
        "STATIC_ROOT":env.get("DJANGO_STATIC_ROOT","/app/staticfiles"),
        "CACHES": {
            "default": {
                "BACKEND": "django.core.cache.backends.redis.RedisCache",
                "LOCATION": redis_url,
                "KEY_PREFIX": "sirago-production",
                "OPTIONS": {"socket_connect_timeout": 2, "socket_timeout": 2},
            },
        },
    }
