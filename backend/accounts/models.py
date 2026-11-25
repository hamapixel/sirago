from django.contrib.auth.models import AbstractUser
from django.db import models
class User(AbstractUser):
    # Custom user from the first migration; public registration comes in phase 02.
    class Role(models.TextChoices):
        TRAVELER = "TRAVELER", "Voyageur"
        COMPANY = "COMPANY", "Compagnie"
    role = models.CharField(max_length=16, choices=Role.choices, default=Role.TRAVELER)
    phone = models.CharField(max_length=16, unique=True, null=True, blank=True)
