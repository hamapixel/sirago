from django.conf import settings
from django.core.cache import cache
from django.db import connection
from django.http import JsonResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET

@never_cache
@require_GET
def health(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        if not settings.DEBUG and settings.CACHES["default"]["BACKEND"] == "django.core.cache.backends.redis.RedisCache":
            # A read-only probe still connects to Redis, even if the key is absent.
            cache.get("sirago-health-probe")
    except Exception:
        return JsonResponse({"status":"unavailable"}, status=503)
    return JsonResponse({"status":"ok","service":"sirago"})
