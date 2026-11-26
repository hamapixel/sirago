from django.test import SimpleTestCase
from django.urls import Resolver404, resolve
from core.converters import MAX_BIGINT, BoundedIntegerConverter


class BoundedApiUrlTests(SimpleTestCase):
    routes = (
        "/api/v1/auth/supervision/settlements/{}/",
        "/api/v1/auth/settlements/{}/pdf/",
        "/api/v1/auth/supervision/commissions/{}/",
        "/api/v1/auth/notifications/{}/read/",
        "/api/v1/auth/company/agents/{}/",
        "/api/v1/company/buses/{}/",
        "/api/v1/company/routes/{}/",
        "/api/v1/company/departures/{}/",
        "/api/v1/company/departures/{}/manifest/",
        "/api/v1/company/departures/{}/manifest/pdf/",
        "/api/v1/company/departures/{}/status/",
        "/api/v1/travel/partners/{}/",
        "/api/v1/travel/bookings/{}/",
        "/api/v1/travel/bookings/{}/cancel/",
        "/api/v1/travel/bookings/{}/sandbox-checkout/",
        "/api/v1/travel/bookings/{}/sandbox-checkout/verify/",
        "/api/v1/travel/bookings/{}/simulate-payment/",
        "/api/v1/travel/bookings/{}/report/options/",
        "/api/v1/travel/bookings/{}/report/",
        "/api/v1/travel/bookings/{}/tickets/",
        "/api/v1/travel/bookings/{}/tickets/0/0/pdf/",
    )

    def test_valid_ids_resolve_to_integer(self):
        for route in self.routes:
            for pk in (1, MAX_BIGINT):
                with self.subTest(route=route, pk=pk):
                    self.assertEqual(resolve(route.format(pk)).kwargs["pk"], pk)

    def test_out_of_range_ids_never_reach_views(self):
        for route in self.routes:
            for value in (str(MAX_BIGINT + 1), "9" * 20, "9" * 5000, "-1"):
                with self.subTest(route=route, length=len(value)):
                    with self.assertRaises(Resolver404):
                        resolve(route.format(value))

    def test_ticket_indices_allow_zero_and_reject_overflow(self):
        base = "/api/v1/travel/bookings/1/tickets/"
        self.assertEqual(resolve(base + "0/0/pdf/").kwargs,
                         {"pk": 1, "leg": 0, "passenger": 0})
        for path in (f"{MAX_BIGINT + 1}/0/pdf/", f"0/{MAX_BIGINT + 1}/pdf/"):
            with self.assertRaises(Resolver404):
                resolve(base + path)

    def test_invalid_ids_return_http_404(self):
        for route in (self.routes[0], self.routes[5], self.routes[13]):
            url = route.format(MAX_BIGINT + 1)
            self.assertEqual(self.client.get(url).status_code, 404)
            self.assertEqual(self.client.post(url).status_code, 404)

    def test_converter_rejects_invalid_reverse_values(self):
        converter = BoundedIntegerConverter()
        self.assertEqual(converter.to_url(0), "0")
        self.assertEqual(converter.to_url(MAX_BIGINT), str(MAX_BIGINT))
        for value in (-1, MAX_BIGINT + 1, True, "1.0", "９", "0" * 20):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    converter.to_url(value)
