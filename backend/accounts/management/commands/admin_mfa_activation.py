"""Trusted operator bootstrap; never expose this command as an HTTP endpoint."""
import secrets
import uuid
from datetime import timedelta
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from accounts.models import AdminMFA, User
from accounts.mfa import digest, event


class Command(BaseCommand):
    help = "Generate a private 15-minute activation code for an existing superuser."

    def add_arguments(self, parser):
        parser.add_argument("username")
        parser.add_argument("--reset", action="store_true", help="Explicitly revoke enrolled MFA and existing admin sessions.")

    def handle(self, *args, **options):
        with transaction.atomic():
            user = User.objects.select_for_update().filter(
                username=options["username"], is_active=True, is_superuser=True).first()
            if user is None:
                raise CommandError("Superadministrateur actif introuvable.")
            state, _ = AdminMFA.objects.get_or_create(user=user)
            if state.enabled and not options["reset"]:
                raise CommandError("2FA déjà activée. Réinitialisation explicite requise.")
            token = secrets.token_hex(24)
            state.enabled = False
            state.encrypted_secret = ""
            state.recovery_hashes = []
            state.last_step = -1
            state.version = uuid.uuid4()
            state.enrollment_hash = digest(token)
            state.enrollment_expires = timezone.now() + timedelta(minutes=15)
            state.save()
            event(user, "OPERATOR_RESET" if options["reset"] else "ACTIVATION_ISSUED")
        self.stdout.write("Code privé valable 15 minutes, à saisir après le mot de passe :")
        self.stdout.write(token)
