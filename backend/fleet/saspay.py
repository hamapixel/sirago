"""SasPay sandbox diagnostics. Never initiates a debit."""
import json
import re
from decimal import Decimal, InvalidOperation
from urllib.parse import urlsplit
from uuid import UUID
from urllib.error import HTTPError, URLError
from urllib.request import Request, build_opener, HTTPRedirectHandler

SANDBOX_URL = "https://sandbox-api.saspay.me/api/v1"
TARGET_NETWORKS = ("orange_ml", "moov_ml")


class SasPayError(Exception):
    pass


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def sandbox_networks(api_key):
    if not re.fullmatch(r"sk_test_[A-Za-z0-9_-]+", api_key or ""):
        raise SasPayError("Configurez une clé Sandbox sk_test_ dans SASPAY_API_KEY.")
    opener = build_opener(NoRedirect())
    result = {}
    for page in range(1, 21):
        request = Request(
            f"{SANDBOX_URL}/networks/?page={page}&page_size=100",
            headers={"Authorization": f"Bearer {api_key}", "Accept": "application/json"},
            method="GET",
        )
        try:
            with opener.open(request, timeout=10) as response:
                raw = response.read(2_000_001)
                if len(raw) > 2_000_000:
                    raise SasPayError("Réponse SasPay trop volumineuse.")
                payload = json.loads(raw)
        except HTTPError as exc:
            raise SasPayError(f"SasPay : HTTP {exc.code}. Vérifiez la clé et le compte marchand.") from None
        except (URLError, TimeoutError, OSError, ValueError):
            raise SasPayError("Impossible de lire le catalogue SasPay.") from None
        if isinstance(payload, dict) and "data" in payload:
            if payload.get("success") is False:
                raise SasPayError("SasPay a refusé la requête.")
            payload = payload["data"]
        if not isinstance(payload, dict) or not isinstance(payload.get("results"), list) or "next" not in payload:
            raise SasPayError("Format du catalogue SasPay inattendu.")
        for entry in payload["results"]:
            if isinstance(entry, dict) and entry.get("code") in TARGET_NETWORKS:
                if not isinstance(entry.get("is_active"), bool):
                    raise SasPayError("Statut de réseau SasPay inattendu.")
                result[entry["code"]] = entry["is_active"]
        if not payload["next"]:
            return {code: result.get(code) for code in TARGET_NETWORKS}
    raise SasPayError("Pagination SasPay incomplète.")


def _checkout_request(api_key, path, payload=None):
    if not re.fullmatch(r"sk_test_[A-Za-z0-9_-]+", api_key or ""):
        raise SasPayError("Configurez une clé Sandbox sk_test_ dans SASPAY_API_KEY.")
    request = Request(
        SANDBOX_URL + path,
        headers={"Authorization": f"Bearer {api_key}", "Accept": "application/json", "Content-Type": "application/json"},
        data=json.dumps(payload).encode("utf-8") if payload is not None else None,
        method="POST" if payload is not None else "GET",
    )
    try:
        with build_opener(NoRedirect()).open(request, timeout=15) as response:
            raw = response.read(200001)
            if len(raw) > 200000:
                raise SasPayError("Réponse Checkout trop volumineuse.")
            value = json.loads(raw)
    except HTTPError as exc:
        raise SasPayError(f"Checkout Sandbox : HTTP {exc.code}. Vérifiez le tableau de bord avant toute nouvelle tentative.") from None
    except (URLError, TimeoutError, OSError, ValueError):
        raise SasPayError("Réponse Checkout indisponible. Vérifiez le tableau de bord avant toute nouvelle tentative.") from None
    if isinstance(value, dict) and "data" in value:
        if value.get("success") is not True:
            raise SasPayError("SasPay a refusé le Checkout.")
        value = value["data"]
    if not isinstance(value, dict):
        raise SasPayError("Format Checkout inattendu.")
    return value


def _session_id(value):
    try:
        return str(UUID(str(value)))
    except (TypeError, ValueError, AttributeError):
        raise SasPayError("Identifiant de session invalide.") from None


def sandbox_checkout_probe(api_key):
    """Create one unpaid diagnostic session only; never retry or visit its URL."""
    value = _checkout_request(api_key, "/checkout-sessions/", {
        "amount": "1000.00", "currency": "XOF", "country": "ML",
        "description": "SiraGo - Diagnostic Sandbox (sans reservation)",
        "customer_email": "sirago-test@example.com", "customer_name": "SiraGo Test",
    })
    session_id = _session_id(value.get("id"))
    try:
        url = urlsplit(value.get("checkout_url", ""))
        safe = (url.scheme == "https" and url.netloc == "sandbox-checkout.saspay.me"
                and url.path.startswith("/") and bool(url.path.strip("/")) and not url.fragment)
        amount_ok = Decimal(str(value.get("amount"))) == Decimal("1000.00")
    except (ValueError, TypeError, InvalidOperation):
        safe = amount_ok = False
    if not safe:
        raise SasPayError("URL Checkout non conforme au Sandbox. Ne payez pas cette session.")
    if not amount_ok or value.get("currency") != "XOF" or value.get("country") != "ML" or value.get("status") != "PENDING":
        raise SasPayError("Montant, devise, pays ou statut Checkout inattendu.")
    return session_id


def sandbox_checkout_status(api_key, session_id):
    session_id = _session_id(session_id)
    value = _checkout_request(api_key, f"/checkout-sessions/{session_id}/status/")
    if _session_id(value.get("id")) != session_id or value.get("status") not in ("PENDING", "PAID", "EXPIRED", "CANCELLED"):
        raise SasPayError("Statut Checkout inattendu.")
    return value["status"]


def sandbox_enabled():
    import os
    from django.conf import settings
    return (settings.DEBUG and os.getenv("SIRAGO_ENV")!="production"
            and os.getenv("SIRAGO_ENABLE_SASPAY_SANDBOX")=="1"
            and bool(re.fullmatch(r"sk_test_[A-Za-z0-9_-]+",os.getenv("SASPAY_API_KEY",""))))


def checkout_booking_reference(booking):
    return f"SG-TEST-{booking.pk}-{booking.request_id}"


def _validated_booking_session(value, booking, amount):
    from django.utils.dateparse import parse_datetime
    try:
        raw_url=value["checkout_url"]
        url=urlsplit(raw_url)
        safe=(isinstance(raw_url,str) and len(raw_url)<=1000 and url.scheme=="https"
              and url.netloc=="sandbox-checkout.saspay.me" and bool(url.path.strip("/"))
              and not url.fragment and not any(ord(c)<33 for c in raw_url))
        expires=parse_datetime(value["expires_at"])
        valid=(safe and Decimal(str(value["amount"]))==Decimal(amount)
               and value["currency"]=="XOF" and value["country"]=="ML"
               and value["metadata"]["sirago_reference"]==checkout_booking_reference(booking)
               and expires is not None and expires.tzinfo is not None and expires<=booking.expires_at)
    except (KeyError,ValueError,TypeError,InvalidOperation,AttributeError,OverflowError):
        valid=False
    if not valid:
        raise SasPayError("Session Sandbox non conforme à la réservation.")
    return _session_id(value.get("id"))


def create_booking_checkout(api_key, booking, amount):
    import os
    from django.utils import timezone
    payload={
        "amount":f"{amount}.00","currency":"XOF","country":"ML",
        "description":f"SiraGo TEST - Reservation {booking.pk}",
        "customer_email":"sirago-test@example.com","customer_name":"SiraGo Test",
        "metadata":{"sirago_reference":checkout_booking_reference(booking)},
        "expires_at":booking.expires_at.isoformat(),
    }
    # Fixed local return origin, not a user-supplied redirect. Opt in for desktop tests.
    if os.getenv("SIRAGO_SASPAY_LOCAL_RETURN")=="1":
        payload["return_url"]=f"http://localhost:8030/app/?view=tickets&booking={booking.pk}"
    value=_checkout_request(api_key,"/checkout-sessions/",payload)
    sid=_validated_booking_session(value,booking,amount)
    from django.utils.dateparse import parse_datetime
    if value.get("status")!="PENDING" or parse_datetime(value["expires_at"])<=timezone.now():
        raise SasPayError("Session Sandbox non disponible.")
    return sid,value["checkout_url"]


def inspect_booking_checkout(api_key, booking, attempt):
    sid=_session_id(attempt.provider_id)
    value=_checkout_request(api_key,f"/checkout-sessions/{sid}/")
    if _validated_booking_session(value,booking,attempt.amount)!=sid:
        raise SasPayError("Identifiant Checkout inattendu.")
    status=value.get("status")
    if status not in ("PENDING","PAID","EXPIRED","CANCELLED"):
        raise SasPayError("Statut Checkout inattendu.")
    txid=None
    if status=="PAID":
        result=_checkout_request(api_key,f"/checkout-sessions/{sid}/status/")
        if (_session_id(result.get("id"))!=sid or result.get("status")!="PAID"
            or result.get("transaction_status")!="SUCCESS"):
            raise SasPayError("Transaction Sandbox non confirmée.")
        txid=_session_id(result.get("transaction_id"))
        from django.utils.dateparse import parse_datetime
        try:
            paid_at=parse_datetime(value["paid_at"])
        except (KeyError,ValueError,TypeError):
            paid_at=None
        if paid_at is None or paid_at.tzinfo is None:
            raise SasPayError("Date de paiement Sandbox invalide.")
        if paid_at>booking.expires_at:
            return "LATE_PAID",txid
    return status,txid


def verify_booking_checkout(api_key, booking, attempt):
    return inspect_booking_checkout(api_key,booking,attempt)[0]


def sandbox_tickets_enabled():
    import os
    from django.conf import settings
    return sandbox_enabled() and settings.SIRAGO_ENABLE_SIMULATED_PAYMENTS and os.getenv("SIRAGO_ENABLE_SASPAY_TICKETS")=="1"
