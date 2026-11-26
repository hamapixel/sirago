import os
from django.core.management.base import BaseCommand, CommandError
from fleet.saspay import sandbox_networks, SasPayError


class Command(BaseCommand):
    help = "Vérifie le catalogue SasPay Sandbox sans initier de paiement."

    def handle(self, *args, **options):
        try:
            networks = sandbox_networks(os.environ.get("SASPAY_API_KEY", ""))
        except SasPayError as exc:
            raise CommandError(str(exc)) from None
        self.stdout.write(self.style.SUCCESS("Connexion API Sandbox : OK"))
        for code, active in networks.items():
            self.stdout.write(f"{code}: " + ("actif" if active is True else "inactif" if active is False else "absent"))
        self.stdout.write("Catalogue uniquement : éligibilité marchand à confirmer. Aucun débit.")
