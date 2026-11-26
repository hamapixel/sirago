import os
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent
DEBUG = os.environ.get("DJANGO_DEBUG") == "1"
SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "backend"]
INSTALLED_APPS = ["config.admin_apps.SiraGoAdminConfig", "django.contrib.auth", "django.contrib.contenttypes", "django.contrib.sessions", "django.contrib.messages", "django.contrib.staticfiles", "rest_framework", "accounts", "core", "fleet"]
AUTH_USER_MODEL = "accounts.User"
MIDDLEWARE = ["django.middleware.security.SecurityMiddleware", "django.contrib.sessions.middleware.SessionMiddleware", "django.middleware.common.CommonMiddleware", "django.middleware.csrf.CsrfViewMiddleware", "django.contrib.auth.middleware.AuthenticationMiddleware", "django.contrib.messages.middleware.MessageMiddleware", "django.middleware.clickjacking.XFrameOptionsMiddleware"]
ROOT_URLCONF = "config.urls"
TEMPLATES = [{"BACKEND":"django.template.backends.django.DjangoTemplates","APP_DIRS":True,"OPTIONS":{"context_processors":["django.template.context_processors.request","django.contrib.auth.context_processors.auth","django.contrib.messages.context_processors.messages"]}}]
DATABASES = {"default":{"ENGINE":"django.db.backends.postgresql","NAME":os.environ.get("POSTGRES_DB","sirago"),"USER":os.environ.get("POSTGRES_USER","sirago"),"PASSWORD":os.environ["POSTGRES_PASSWORD"],"HOST":os.environ.get("DB_HOST","db"),"PORT":"5432"}}
AUTH_PASSWORD_VALIDATORS = [{"NAME":"django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},{"NAME":"django.contrib.auth.password_validation.MinimumLengthValidator"},{"NAME":"django.contrib.auth.password_validation.CommonPasswordValidator"},{"NAME":"django.contrib.auth.password_validation.NumericPasswordValidator"}]
LANGUAGE_CODE = "fr"
TIME_ZONE = "Africa/Bamako"
USE_I18N = True
USE_TZ = True
STATIC_URL = "/static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
CSRF_TRUSTED_ORIGINS = ["http://localhost:8030", "http://127.0.0.1:8030"] if DEBUG else []

# Local single-process throttling; use a shared cache and edge throttling in production.
CSRF_FAILURE_VIEW = "accounts.views.csrf_failure"
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"
if DEBUG:
    CSRF_TRUSTED_ORIGINS += ["http://localhost:8035", "http://127.0.0.1:8035"]

# Explicit opt-in, always disabled when DEBUG is false.
SIRAGO_ENABLE_SIMULATED_PAYMENTS = os.environ.get("SIRAGO_ENABLE_SIMULATED_PAYMENTS") == "1"

# Explicit production profile; default Docker development workflow is unchanged.
if os.environ.get("SIRAGO_ENV") == "production":
    from .production import production_settings
    globals().update(production_settings(os.environ))

    MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")
