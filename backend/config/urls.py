from django.contrib import admin
from django.urls import path, include
from core.views import health
urlpatterns = [path("admin/", admin.site.urls), path("api/v1/auth/", include("accounts.urls")), path("api/v1/company/", include("fleet.urls")), path("api/v1/travel/", include("fleet.public_urls")), path("api/v1/health/", health)]
