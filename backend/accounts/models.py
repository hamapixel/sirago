from django.contrib.auth.models import AbstractUser
from django.db import models
class User(AbstractUser):
    # Custom user from the first migration; public registration comes in phase 02.
    class Role(models.TextChoices):
        TRAVELER = "TRAVELER", "Voyageur"
        COMPANY = "COMPANY", "Compagnie"
    role = models.CharField(max_length=16, choices=Role.choices, default=Role.TRAVELER)
    phone = models.CharField(max_length=16, unique=True, null=True, blank=True)

    class Meta(AbstractUser.Meta):
        constraints = [models.UniqueConstraint(models.functions.Lower("email"), condition=~models.Q(email=""), name="unique_nonempty_email_ci")]

class Company(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "En attente"
        VERIFIED = "VERIFIED", "Validée"
        REJECTED = "REJECTED", "Rejetée"
        SUSPENDED = "SUSPENDED", "Suspendue"
    owner = models.OneToOneField(User, on_delete=models.PROTECT, related_name="company")
    name = models.CharField(max_length=150)
    city = models.CharField(max_length=100)
    address = models.CharField(max_length=250)
    registration_number = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class CompanyAgent(models.Model):
    class Role(models.TextChoices):
        CLERK = "CLERK", "Guichetier"
        CONTROLLER = "CONTROLLER", "Contrôleur"

    user = models.OneToOneField(User, on_delete=models.PROTECT, related_name="company_agent")
    company = models.ForeignKey(Company, on_delete=models.PROTECT, related_name="agents")
    role = models.CharField(max_length=16, choices=Role.choices)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.CheckConstraint(condition=models.Q(role__in=["CLERK","CONTROLLER"]),name="accounts_agent_role")]


class Notification(models.Model):
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sirago_notifications")
    kind = models.CharField(max_length=32)
    title = models.CharField(max_length=120)
    message = models.CharField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["recipient", "-id"], name="notif_recipient_recent"),
            models.Index(fields=["recipient", "read_at"], name="notif_recipient_read"),
        ]


class SupportRequest(models.Model):
    class Category(models.TextChoices):
        BOOKING = "BOOKING", "Réservation et billet"
        REPORT = "REPORT", "Report de voyage"
        PAYMENT = "PAYMENT", "Paiement"
        ACCOUNT = "ACCOUNT", "Compte et accès"
        TECHNICAL = "TECHNICAL", "Problème technique"
        OTHER = "OTHER", "Autre"
    class Status(models.TextChoices):
        OPEN = "OPEN", "Reçue"
        IN_PROGRESS = "IN_PROGRESS", "En cours"
        RESOLVED = "RESOLVED", "Résolue"
    requester = models.ForeignKey(User, on_delete=models.PROTECT, related_name="support_requests")
    reference = models.UUIDField(unique=True, editable=False)
    category = models.CharField(max_length=16, choices=Category.choices)
    subject = models.CharField(max_length=120)
    message = models.TextField(max_length=2000)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.OPEN)
    reply = models.TextField(max_length=4000, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [models.Index(fields=["requester","-id"], name="support_requester_recent")]

    def __str__(self):
        return f"SG-{self.reference.hex[:12].upper()}"
