from django.db import models
from django.db.models import Q, F
from accounts.models import Company

class Bus(models.Model):
    company = models.ForeignKey(Company, on_delete=models.PROTECT, related_name="buses")
    name = models.CharField(max_length=100)
    plate = models.CharField(max_length=40)
    capacity = models.PositiveIntegerField()
    active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["company", "plate"], name="fleet_unique_company_plate"),
            models.CheckConstraint(condition=Q(capacity__gte=1, capacity__lte=100), name="fleet_bus_capacity"),
        ]

    def __str__(self):
        return self.name

class Route(models.Model):
    company = models.ForeignKey(Company, on_delete=models.PROTECT, related_name="routes")
    origin = models.CharField(max_length=100)
    destination = models.CharField(max_length=100)
    boarding_point = models.CharField(max_length=200)
    arrival_point = models.CharField(max_length=200)
    duration_minutes = models.PositiveIntegerField()
    price = models.PositiveIntegerField()
    active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=~Q(origin=F("destination")), name="fleet_route_distinct_cities"),
            models.CheckConstraint(condition=Q(price__gte=1, price__lte=1000000, duration_minutes__gte=1, duration_minutes__lte=2880), name="fleet_route_values"),
        ]

    def __str__(self):
        return f"{self.origin} → {self.destination}"

class Departure(models.Model):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Brouillon"
        PUBLISHED = "PUBLISHED", "Publié"
        SUSPENDED = "SUSPENDED", "Suspendu"
        CANCELLED = "CANCELLED", "Annulé"
    company = models.ForeignKey(Company, on_delete=models.PROTECT, related_name="departures")
    bus = models.ForeignKey(Bus, on_delete=models.PROTECT, related_name="departures")
    route = models.ForeignKey(Route, on_delete=models.PROTECT, related_name="departures")
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    price = models.PositiveIntegerField()
    capacity = models.PositiveIntegerField()
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.DRAFT)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=Q(ends_at__gt=F("starts_at")), name="fleet_departure_interval"),
            models.CheckConstraint(condition=Q(capacity__gte=1, capacity__lte=100, price__gte=1, price__lte=1000000), name="fleet_departure_values"),
        ]
        indexes = [models.Index(fields=["company","starts_at"], name="fleet_company_start_idx"), models.Index(fields=["bus","starts_at"], name="fleet_bus_start_idx")]

class Booking(models.Model):
    class Status(models.TextChoices):
        HELD = "HELD", "En attente de paiement"
        CANCELLED = "CANCELLED", "Annulée"
    traveler = models.ForeignKey("accounts.User", on_delete=models.PROTECT, related_name="bookings")
    request_id = models.UUIDField()
    passengers = models.PositiveIntegerField()
    passenger_names = models.JSONField(default=list, blank=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.HELD)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["traveler","request_id"], name="fleet_booking_request_unique"),
            models.CheckConstraint(condition=Q(passengers__gte=1,passengers__lte=10), name="fleet_booking_passengers"),
        ]

class BookingLeg(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.PROTECT, related_name="legs")
    departure = models.ForeignKey(Departure, on_delete=models.PROTECT, related_name="booking_legs")
    position = models.PositiveSmallIntegerField()
    unit_price = models.PositiveIntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["booking","position"], name="fleet_booking_leg_position"),
            models.UniqueConstraint(fields=["booking","departure"], name="fleet_booking_leg_unique"),
            models.CheckConstraint(condition=Q(position__lte=1,unit_price__gte=1,unit_price__lte=1000000), name="fleet_booking_leg_values"),
        ]
