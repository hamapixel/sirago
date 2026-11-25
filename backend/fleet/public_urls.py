from django.urls import path
from . import public_views
urlpatterns = [path("search/", public_views.search), path("home/", public_views.home)]
