"""Shared provider reconciliation. No real receipt, no ticket after hold expiration."""
import os
from datetime import timedelta
from django.db import transaction, IntegrityError
from django.utils import timezone
from accounts.models import Company, User
from accounts.notifications import notify
from .models import Booking, Departure, SandboxCheckout, SandboxWebhookReceipt
from .saspay import sandbox_tickets_enabled, inspect_booking_checkout, SasPayError
from .ticket_refs import register_refs

def reconcile(pk):
    if not sandbox_tickets_enabled():raise SasPayError("Émission Sandbox désactivée.")
    # Claim briefly, release database locks before remote I/O.
    now=timezone.now()
    with transaction.atomic():
        a=SandboxCheckout.objects.select_for_update().filter(pk=pk,provider_id__isnull=False,status__in=("PENDING","PAID")).first()
        if a is None or a.issued_at or (a.checked_at and a.checked_at>now-timedelta(seconds=5)):return
        a.checked_at=now;a.save(update_fields=["checked_at"])
    status,txid=inspect_booking_checkout(os.environ.get("SASPAY_API_KEY",""),a.booking,a)
    # Same lock ordering as reservation / simulation; company lock protects capacity.
    try:
        with transaction.atomic():
            User.objects.select_for_update().get(pk=a.booking.traveler_id)
            b=Booking.objects.select_for_update().get(pk=a.booking_id)
            current=SandboxCheckout.objects.select_for_update().get(pk=pk)
            if current.issued_at or current.status not in ("PENDING","PAID"):return
            if status not in ("PAID","LATE_PAID"):
                if current.status=="PENDING":current.status=status;current.save(update_fields=["status"])
                return
            if not txid:raise SasPayError("Transaction Sandbox sans identifiant.")
            if current.transaction_id and str(current.transaction_id)!=str(txid):raise SasPayError("Transaction Sandbox incohérente.")
            if SandboxCheckout.objects.filter(transaction_id=txid).exclude(pk=pk).exists():raise SasPayError("Transaction déjà associée.")
            ids=list(b.legs.values_list("departure__company_id",flat=True).distinct())
            list(Company.objects.select_for_update().filter(pk__in=ids).order_by("pk"))
            now=timezone.now()
            legs=list(b.legs.select_related("departure__company","departure__bus","departure__route"))
            current.transaction_id=txid
            if status=="LATE_PAID":
                current.status="LATE_PAID"
            elif (b.status!=Booking.Status.HELD or b.expires_at<=now or not legs or sum(l.total for l in legs)!=current.amount or
                any(l.departure.starts_at<=now or l.departure.status!=Departure.Status.PUBLISHED or l.departure.company.status!=Company.Status.VERIFIED or not l.departure.bus.active or not l.departure.route.active for l in legs)):
                # A hold already released cannot silently regain seats, even if paid earlier.
                current.status="REVIEW_PAID"
            else:
                current.status="PAID";current.issued_at=now
                b.status=Booking.Status.TEST_PAID;b.save(update_fields=["status"])
                register_refs(b,legs)
                notify(b.traveler_id,"TEST_PAYMENT","Billets SasPay TEST disponibles","Paiement Sandbox vérifié. Consultez Mes billets. Aucun débit réel.",booking_id=b.pk)
                for l in legs:
                    d=l.departure
                    notify(d.company.owner_id,"TEST_BOOKING","Nouvelle réservation SasPay TEST",f"{d.route.origin} → {d.route.destination} : {b.passengers} passager(s). Aucun encaissement réel.")
            current.save(update_fields=["status","transaction_id","issued_at"])
            SandboxWebhookReceipt.objects.filter(transaction_id=txid,matched_at__isnull=True).update(matched_at=now)
    except IntegrityError:
        raise SasPayError("Conflit de confirmation Sandbox. Vérification requise.") from None
