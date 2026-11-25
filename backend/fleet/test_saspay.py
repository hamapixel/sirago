import json
from unittest.mock import patch, MagicMock
from urllib.error import HTTPError
from django.test import SimpleTestCase
from fleet.saspay import sandbox_networks, SasPayError


class SasPayDiagnosticTests(SimpleTestCase):
    def response(self, payload):
        response = MagicMock()
        response.__enter__.return_value.read.return_value = json.dumps(payload).encode()
        return response

    @patch("fleet.saspay.build_opener")
    def test_rejects_live_or_missing_key_without_network(self, opener):
        for key in ("", "sk_live_example"):
            with self.assertRaises(SasPayError):
                sandbox_networks(key)
        opener.assert_not_called()

    @patch("fleet.saspay.build_opener")
    def test_paginated_catalogue_uses_only_sandbox_get(self, opener):
        client = opener.return_value
        client.open.side_effect = [
            self.response({"results": [{"code": "orange_ml", "is_active": True}], "next": "https://untrusted.invalid/"}),
            self.response({"success": True, "data": {"results": [{"code": "moov_ml", "is_active": False}], "next": None}}),
        ]
        self.assertEqual(sandbox_networks("sk_test_example"), {"orange_ml": True, "moov_ml": False})
        for i, call in enumerate(client.open.call_args_list, 1):
            request = call.args[0]
            self.assertEqual(request.get_method(), "GET")
            self.assertEqual(request.full_url, f"https://sandbox-api.saspay.me/api/v1/networks/?page={i}&page_size=100")
            self.assertEqual(request.get_header("Authorization"), "Bearer sk_test_example")

    @patch("fleet.saspay.build_opener")
    def test_missing_network_is_not_active(self, opener):
        opener.return_value.open.return_value = self.response({"results": [], "next": None})
        self.assertEqual(sandbox_networks("sk_test_example"), {"orange_ml": None, "moov_ml": None})

    @patch("fleet.saspay.build_opener")
    def test_http_error_does_not_leak_key(self, opener):
        opener.return_value.open.side_effect = HTTPError("https://sandbox-api.saspay.me", 401, "sk_test_example", {}, None)
        with self.assertRaises(SasPayError) as err:
            sandbox_networks("sk_test_example")
        self.assertIn("401", str(err.exception))
        self.assertNotIn("sk_test_example", str(err.exception))
