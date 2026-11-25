from django.urls import path
from . import views
urlpatterns=[
    path("dashboard/",views.overview),
    path("buses/",views.buses),
    path("buses/<int:pk>/",views.buses),
    path("routes/",views.routes),
    path("routes/<int:pk>/",views.routes),
    path("departures/",views.departures),
    path("departures/<int:pk>/",views.departures),
    path("departures/<int:pk>/status/",views.departure_status),
]
