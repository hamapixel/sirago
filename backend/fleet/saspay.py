"""Read-only SasPay sandbox diagnostics. No payment initiation."""
import json
import re
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
