from django.urls import path
from . import views, boarding_views, manifest_views
urlpatterns=[
    path("dashboard/",views.overview),
    path("boarding/lookup/",boarding_views.lookup),
    path("boarding/validate/",boarding_views.validate),
    path("boarding/history/",boarding_views.history),
    path("reservations/",views.reservations),
    path("buses/",views.buses),
    path("buses/<int:pk>/",views.buses),
    path("routes/",views.routes),
    path("routes/<int:pk>/",views.routes),
    path("departures/",views.departures),
    path("departures/publish-batch/",views.publish_batch),
    path("departures/<int:pk>/",views.departures),
    path("departures/<int:pk>/manifest/",manifest_views.manifest),
    path("departures/<int:pk>/manifest/pdf/",manifest_views.manifest_pdf),
    path("departures/<int:pk>/status/",views.departure_status),
]
