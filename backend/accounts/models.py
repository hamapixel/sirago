import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.crypto import salted_hmac
class User(AbstractUser):
    # Custom user from the first migration; public registration comes in phase 02.
    class Role(models.TextChoices):
        TRAVELER = "TRAVELER", "Voyageur"
        COMPANY = "COMPANY", "Compagnie"
    role = models.CharField(max_length=16, choices=Role.choices, default=Role.TRAVELER)
    phone = models.CharField(max_length=16, unique=True, null=True, blank=True)
    session_version = models.PositiveBigIntegerField(default=0, editable=False)

    def _get_session_auth_hash(self, secret=None):
        # Preserve existing sessions until an explicit administrative revocation.
        if self.session_version == 0:
            return super()._get_session_auth_hash(secret=secret)
        return salted_hmac("sirago.user.session.v1", f"{self.password}:{self.session_version}",
                           secret=secret, algorithm="sha256").hexdigest()

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
    logo = models.TextField(blank=True, default="", editable=False)
    banner = models.TextField(blank=True, default="", editable=False)
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
    booking_id = models.PositiveBigIntegerField(null=True, blank=True)
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


class CompanyCommission(models.Model):
    company = models.OneToOneField(Company, on_delete=models.PROTECT, related_name="commission_policy")
    rate_bps = models.PositiveSmallIntegerField()
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.CheckConstraint(condition=models.Q(rate_bps__lte=1000), name="commission_rate_max_10")]


class CommissionChange(models.Model):
    company = models.ForeignKey(Company, on_delete=models.PROTECT, related_name="commission_changes")
    actor = models.ForeignKey(User, on_delete=models.PROTECT)
    previous_bps = models.PositiveSmallIntegerField(null=True)
    new_bps = models.PositiveSmallIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=models.Q(new_bps__lte=1000), name="commission_change_new_max_10"),
            models.CheckConstraint(condition=models.Q(previous_bps__isnull=True)|models.Q(previous_bps__lte=1000), name="commission_change_old_max_10"),
        ]


class PushSubscription(models.Model):
    recipient = models.ForeignKey(User, on_delete=models.CASCADE)
    session_key = models.CharField(max_length=40)
    endpoint = models.URLField(max_length=2048, unique=True)
    p256dh = models.CharField(max_length=100)
    auth = models.CharField(max_length=40)
    created_at = models.DateTimeField(auto_now_add=True)


class PushDelivery(models.Model):
    subscription = models.ForeignKey(PushSubscription, on_delete=models.CASCADE)
    notification = models.ForeignKey(Notification, on_delete=models.CASCADE)
    attempts = models.PositiveSmallIntegerField(default=0)
    next_attempt = models.DateTimeField(db_index=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=["subscription", "notification"], name="push_unique_delivery")]


class AdminMFA(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="admin_mfa")
    enabled = models.BooleanField(default=False)
    encrypted_secret = models.TextField(blank=True, default="")
    enrollment_hash = models.CharField(max_length=64, blank=True, default="")
    enrollment_expires = models.DateTimeField(null=True, blank=True)
    last_step = models.BigIntegerField(default=-1)
    recovery_hashes = models.JSONField(default=list)
    version = models.UUIDField(default=uuid.uuid4, editable=False)


class AdminMFAEvent(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    kind = models.CharField(max_length=32)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

class AdminAction(models.Model):
    actor = models.ForeignKey(User, on_delete=models.PROTECT, related_name="admin_actions")
    target_type = models.CharField(max_length=16)
    target_id = models.PositiveBigIntegerField()
    before = models.CharField(max_length=32)
    after = models.CharField(max_length=32)
    reason = models.CharField(max_length=300)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
