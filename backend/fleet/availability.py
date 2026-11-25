from django.db.models import OuterRef, Subquery, Sum, Value, IntegerField, F, Case, When, Q
from django.db.models.functions import Coalesce
from .models import Booking, BookingLeg

def active_legs(now):
    return BookingLeg.objects.filter(Q(booking__status=Booking.Status.HELD, booking__expires_at__gt=now) | Q(booking__status=Booking.Status.TEST_PAID))

def with_remaining(qs, now):
    legs=active_legs(now).filter(departure_id=OuterRef("pk")).order_by().values("departure_id")
    used=legs.annotate(n=Sum("booking__passengers")).values("n")
    premium=legs.annotate(n=Sum("premium_count")).values("n")
    return qs.annotate(remaining=F("capacity")-Coalesce(Subquery(used,output_field=IntegerField()),Value(0)),
        premium_remaining=F("premium_capacity")-Coalesce(Subquery(premium,output_field=IntegerField()),Value(0))).annotate(
        standard_remaining=F("remaining")-F("premium_remaining")).annotate(
        from_price=Case(When(standard_remaining__gt=0,then=F("price")),default=F("premium_price"),output_field=IntegerField()))
