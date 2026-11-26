from django.urls import path
from . import views, boarding_views, manifest_views, finance_views
urlpatterns=[
    path("dashboard/",views.overview),
    path("finance/",finance_views.finance),
    path("boarding/lookup/",boarding_views.lookup),
    path("boarding/validate/",boarding_views.validate),
    path("boarding/history/",boarding_views.history),
    path("reservations/",views.reservations),
    path("reservations/<bounded_int:pk>/",views.reservations),
    path("buses/",views.buses),
    path("buses/<bounded_int:pk>/",views.buses),
    path("routes/",views.routes),
    path("routes/<bounded_int:pk>/",views.routes),
    path("departures/",views.departures),
    path("departures/publish-batch/",views.publish_batch),
    path("departures/<bounded_int:pk>/",views.departures),
    path("departures/<bounded_int:pk>/manifest/",manifest_views.manifest),
    path("departures/<bounded_int:pk>/manifest/pdf/",manifest_views.manifest_pdf),
    path("departures/<bounded_int:pk>/status/",views.departure_status),
]
