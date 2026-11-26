from django.contrib import admin
from django.urls import path, include, register_converter
from core.views import health
from core.converters import BoundedIntegerConverter

register_converter(BoundedIntegerConverter, "bounded_int")
urlpatterns = [path("admin/", admin.site.urls), path("api/v1/auth/", include("accounts.urls")), path("api/v1/company/", include("fleet.urls")), path("api/v1/travel/", include("fleet.public_urls")), path("api/v1/health/", health)]
