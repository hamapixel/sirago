from django.db.models import OuterRef, Subquery, Sum, Value, IntegerField, F
from django.db.models.functions import Coalesce
from .models import Booking, BookingLeg

def active_legs(now):
    return BookingLeg.objects.filter(booking__status=Booking.Status.HELD, booking__expires_at__gt=now)

def with_remaining(qs, now):
    used=active_legs(now).filter(departure_id=OuterRef("pk")).order_by().values("departure_id").annotate(n=Sum("booking__passengers")).values("n")
    return qs.annotate(remaining=F("capacity")-Coalesce(Subquery(used,output_field=IntegerField()),Value(0)))
