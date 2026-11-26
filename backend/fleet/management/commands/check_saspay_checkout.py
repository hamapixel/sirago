import os
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from fleet.saspay import SasPayError, sandbox_checkout_probe, sandbox_checkout_status


class Command(BaseCommand):
    help = "Diagnostic Checkout Sandbox isole : creation non payee ou lecture du statut."

    def add_arguments(self, parser):
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument("--create", action="store_true", help="Cree une seule session de diagnostic non payee.")
        group.add_argument("--session", help="Identifiant UUID d'une session a verifier.")

    def handle(self, *args, **options):
        if not settings.DEBUG or os.environ.get("SIRAGO_ENV") == "production":
            raise CommandError("Diagnostic reserve au developpement.")
        key = os.environ.get("SASPAY_API_KEY", "")
        try:
            if options["create"]:
                session = sandbox_checkout_probe(key)
                self.stdout.write(self.style.SUCCESS("Creation Checkout Sandbox : OK"))
                self.stdout.write(f"Session : {session}")
                self.stdout.write("Montant : 1000 XOF | Pays : ML | Statut initial : PENDING")
                self.stdout.write("Domaine Checkout : sandbox-checkout.saspay.me")
                self.stdout.write("Session non payee. Aucun billet ni reservation cree.")
            else:
                status = sandbox_checkout_status(key, options["session"])
                self.stdout.write(f"Statut Sandbox : {status}")
                self.stdout.write("Diagnostic uniquement. Aucun billet emis.")
        except SasPayError as exc:
            raise CommandError(str(exc)) from None
