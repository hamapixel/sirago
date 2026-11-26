import time
from datetime import timedelta
from django.core.management.base import BaseCommand,CommandError
from django.db import close_old_connections
from django.db.models import Q,F
from django.utils import timezone
from fleet.models import SandboxCheckout,SandboxWebhookReceipt
from fleet.saspay import sandbox_tickets_enabled,SasPayError
from fleet.sandbox_reconcile import reconcile

class Command(BaseCommand):
    help="Reconciliation automatique Sandbox (worker local, aucun paiement réel)."
    def add_arguments(self,parser):
        parser.add_argument("--watch",action="store_true")
    def handle(self,*args,**options):
        if not sandbox_tickets_enabled():raise CommandError("Émission de billets Sandbox désactivée.")
        self.stdout.write("Worker SasPay Sandbox actif.")
        while True:
            close_old_connections()
            now=timezone.now()
            # Webhook receipts are durable hints; polling also recovers missing deliveries.
            # Prioritize fresh reservations before older unpaid sessions.
            due=SandboxCheckout.objects.filter(issued_at__isnull=True,provider_id__isnull=False,status__in=("PENDING","PAID")).filter(Q(checked_at__isnull=True)|Q(checked_at__lte=now-timedelta(seconds=10)))
            fresh=list(due.filter(booking__expires_at__gt=now).order_by(F("checked_at").asc(nulls_first=True),"pk").values_list("pk",flat=True)[:8])
            old=list(due.filter(booking__expires_at__lte=now).order_by(F("checked_at").asc(nulls_first=True),"pk").values_list("pk",flat=True)[:2])
            for pk in fresh+old:
                try:reconcile(pk)
                except SasPayError:self.stderr.write(f"Session locale {pk} : vérification indisponible; nouvelle tentative ultérieure.")
            if not options["watch"]:break
            time.sleep(5)
