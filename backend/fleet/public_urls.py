from django.urls import path
from . import public_views, booking_views
urlpatterns = [path("search/", public_views.search), path("home/", public_views.home), path("quote/", booking_views.quote), path("bookings/", booking_views.mine), path("bookings/reserve/", booking_views.reserve), path("bookings/<int:pk>/", booking_views.detail), path("bookings/<int:pk>/cancel/", booking_views.cancel), path("bookings/<int:pk>/simulate-payment/", booking_views.simulate_payment)]
