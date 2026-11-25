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
