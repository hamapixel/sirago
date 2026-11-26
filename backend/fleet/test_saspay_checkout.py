import json
from unittest.mock import patch, MagicMock
from django.test import SimpleTestCase, override_settings
from django.core.management import call_command, CommandError
from fleet.saspay import SasPayError, sandbox_checkout_probe, sandbox_checkout_status

SID = "c9a17e2c-4b1a-4f0e-9c3d-2a1b3c4d5e6f"
BASE = {"id": SID, "amount": "1000.00", "currency": "XOF", "country": "ML", "status": "PENDING",
        "checkout_url": "https://sandbox-checkout.saspay.me/checkout/example"}


class CheckoutProbeTests(SimpleTestCase):
    def response(self, payload):
        r = MagicMock()
        r.__enter__.return_value.read.return_value = json.dumps(payload).encode()
        return r

    @patch("fleet.saspay.build_opener")
    def test_create_uses_only_sandbox_and_fixed_dummy_data(self, opener):
        opener.return_value.open.return_value = self.response({"success": True, "data": BASE})
        self.assertEqual(sandbox_checkout_probe("sk_test_example"), SID)
        request = opener.return_value.open.call_args.args[0]
        self.assertEqual(request.full_url, "https://sandbox-api.saspay.me/api/v1/checkout-sessions/")
        self.assertEqual(request.get_method(), "POST")
        body = json.loads(request.data)
        self.assertEqual((body["amount"], body["currency"], body["country"]), ("1000.00", "XOF", "ML"))
        self.assertNotIn("customer_phone", body)
        self.assertEqual(opener.return_value.open.call_count, 1)

    @patch("fleet.saspay.build_opener")
    def test_live_key_refused_before_network(self, opener):
        with self.assertRaises(SasPayError):
            sandbox_checkout_probe("sk_live_example")
        opener.assert_not_called()

    @patch("fleet.saspay.build_opener")
    def test_rejects_live_and_spoofed_checkout(self, opener):
        for url in ("https://pay.saspay.me/checkout/x", "https://sandbox-checkout.saspay.me.evil.example/x",
                    "http://sandbox-checkout.saspay.me/x", "https://sandbox-checkout.saspay.me@evil.example/x"):
            opener.return_value.open.return_value = self.response({**BASE, "checkout_url": url})
            with self.assertRaises(SasPayError):
                sandbox_checkout_probe("sk_test_example")

    @patch("fleet.saspay.build_opener")
    def test_rejects_wrong_session_data(self, opener):
        for extra in ({"amount": "1"}, {"currency": "USD"}, {"country": "BJ"}, {"status": "PAID"}):
            opener.return_value.open.return_value = self.response({**BASE, **extra})
            with self.assertRaises(SasPayError):
                sandbox_checkout_probe("sk_test_example")

    @patch("fleet.saspay.build_opener")
    def test_status_read_and_invalid_id(self, opener):
        opener.return_value.open.return_value = self.response({"success": True, "data": {"id": SID, "status": "PENDING"}})
        self.assertEqual(sandbox_checkout_status("sk_test_example", SID), "PENDING")
        request = opener.return_value.open.call_args.args[0]
        self.assertEqual(request.get_method(), "GET")
        self.assertEqual(request.full_url, f"https://sandbox-api.saspay.me/api/v1/checkout-sessions/{SID}/status/")
        with self.assertRaises(SasPayError):
            sandbox_checkout_status("sk_test_example", "../invalid")
        self.assertEqual(opener.return_value.open.call_count, 1)

    @override_settings(DEBUG=False)
    @patch("fleet.management.commands.check_saspay_checkout.sandbox_checkout_probe")
    def test_command_disabled_outside_debug(self, probe):
        with self.assertRaises(CommandError):
            call_command("check_saspay_checkout", "--create")
        probe.assert_not_called()
