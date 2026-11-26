from django.db import models
from django.db.models import Q, F
from accounts.models import Company

class Bus(models.Model):
    company = models.ForeignKey(Company, on_delete=models.PROTECT, related_name="buses")
    name = models.CharField(max_length=100)
    plate = models.CharField(max_length=40)
    capacity = models.PositiveIntegerField()
    premium_capacity = models.PositiveIntegerField(default=0)
    active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["company", "plate"], name="fleet_unique_company_plate"),
            models.CheckConstraint(condition=Q(capacity__gte=1, capacity__lte=100), name="fleet_bus_capacity"),
            models.CheckConstraint(condition=Q(premium_capacity__lt=F("capacity")), name="fleet_bus_premium_capacity"),
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
    premium_capacity = models.PositiveIntegerField(default=0)
    premium_price = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.DRAFT)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=Q(ends_at__gt=F("starts_at")), name="fleet_departure_interval"),
            models.CheckConstraint(condition=Q(capacity__gte=1, capacity__lte=100, price__gte=1, price__lte=1000000), name="fleet_departure_values"),
            models.CheckConstraint(condition=Q(premium_capacity__lt=F("capacity")) & (Q(premium_capacity=0,premium_price=0) | Q(premium_capacity__gt=0,premium_price__gte=F("price"),premium_price__lte=1000000)), name="fleet_departure_premium_values"),
        ]
        indexes = [models.Index(fields=["company","starts_at"], name="fleet_company_start_idx"), models.Index(fields=["bus","starts_at"], name="fleet_bus_start_idx")]

class Booking(models.Model):
    class Status(models.TextChoices):
        HELD = "HELD", "En attente de paiement"
        TEST_PAID = "TEST_PAID", "Paiement simulé"
        REPORTED = "REPORTED", "Reportée"
        CANCELLED = "CANCELLED", "Annulée"
    traveler = models.ForeignKey("accounts.User", on_delete=models.PROTECT, related_name="bookings")
    request_id = models.UUIDField()
    passengers = models.PositiveIntegerField()
    ticket_mode = models.CharField(max_length=10, choices=[("group","Collectifs"),("individual","Individuels")], default="group")
    passenger_names = models.JSONField(default=list, blank=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.HELD)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["traveler","request_id"], name="fleet_booking_request_unique"),
            models.CheckConstraint(condition=Q(passengers__gte=1,passengers__lte=100), name="fleet_booking_passengers"),
            models.CheckConstraint(condition=Q(ticket_mode__in=["group","individual"]), name="fleet_booking_ticket_mode"),
        ]

class BookingLeg(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.PROTECT, related_name="legs")
    departure = models.ForeignKey(Departure, on_delete=models.PROTECT, related_name="booking_legs")
    position = models.PositiveSmallIntegerField()
    unit_price = models.PositiveIntegerField()
    premium_count = models.PositiveIntegerField(default=0)
    premium_unit_price = models.PositiveIntegerField(default=0)
    premium_positions = models.JSONField(default=list, blank=True)

    @property
    def total(self):
        return self.unit_price*(self.booking.passengers-self.premium_count)+self.premium_unit_price*self.premium_count

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["booking","position"], name="fleet_booking_leg_position"),
            models.UniqueConstraint(fields=["booking","departure"], name="fleet_booking_leg_unique"),
            models.CheckConstraint(condition=Q(position__lte=1,unit_price__gte=1,unit_price__lte=1000000), name="fleet_booking_leg_values"),
            models.CheckConstraint(condition=Q(premium_count__lte=100) & (Q(premium_count=0,premium_unit_price=0) | Q(premium_count__gt=0,premium_unit_price__gte=F("unit_price"),premium_unit_price__lte=1000000)),name="fleet_leg_premium_values"),
        ]


class SimulatedPayment(models.Model):
    """Local test record, never a financial transaction."""
    booking = models.OneToOneField(Booking, on_delete=models.PROTECT, related_name="simulated_payment")
    amount = models.PositiveIntegerField()
    network = models.CharField(max_length=20, choices=[("orange_ml", "Orange Money"), ("moov_ml", "Moov Money")])
    created_at = models.DateTimeField(auto_now_add=True)


class TestTicketReference(models.Model):
    code = models.CharField(max_length=41, unique=True)
    leg = models.ForeignKey(BookingLeg, on_delete=models.PROTECT, related_name="test_ticket_refs")
    anchor = models.PositiveSmallIntegerField()

    class Meta:
        constraints = [models.UniqueConstraint(fields=["leg","anchor"],name="fleet_test_ticket_anchor")]


class TestBoarding(models.Model):
    leg = models.ForeignKey(BookingLeg, on_delete=models.PROTECT, related_name="test_boardings")
    passenger = models.PositiveSmallIntegerField()
    actor = models.ForeignKey("accounts.User", on_delete=models.PROTECT)
    boarded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["leg","passenger"],name="fleet_test_boarding_once")]


class TestTicketReport(models.Model):
    original = models.OneToOneField(Booking, on_delete=models.PROTECT, related_name="outgoing_report")
    replacement = models.OneToOneField(Booking, on_delete=models.PROTECT, related_name="incoming_report")
    retained = models.OneToOneField(Booking, on_delete=models.PROTECT, related_name="retained_report", null=True, blank=True)
    selected_positions = models.JSONField(default=list, blank=True)
    previous_amount = models.PositiveIntegerField()
    new_amount = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)


class SandboxCheckout(models.Model):
    """One provider checkout attempt per local test reservation; never a real receipt."""
    booking = models.OneToOneField(Booking, on_delete=models.PROTECT, related_name="sandbox_checkout")
    amount = models.PositiveIntegerField()
    provider_id = models.UUIDField(null=True, blank=True, unique=True)
    checkout_url = models.URLField(max_length=1000, blank=True)
    status = models.CharField(max_length=16, default="CREATING")
    created_at = models.DateTimeField(auto_now_add=True)
    checked_at = models.DateTimeField(null=True, blank=True)
    transaction_id = models.UUIDField(null=True, blank=True, unique=True)
    issued_at = models.DateTimeField(null=True, blank=True)


class SandboxWebhookReceipt(models.Model):
    transaction_id = models.UUIDField(unique=True)
    received_at = models.DateTimeField(auto_now_add=True)
    matched_at = models.DateTimeField(null=True, blank=True)
