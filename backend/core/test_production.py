from django.test import SimpleTestCase,override_settings
from django.core.exceptions import ImproperlyConfigured
from config.production import production_settings
from fleet.booking_views import simulation_enabled

class ProductionSettingsTests(SimpleTestCase):
    def env(self):
        return {"DJANGO_DEBUG":"0","SIRAGO_ENABLE_SIMULATED_PAYMENTS":"0",
                "DJANGO_SECRET_KEY":"ExampleOnly"+("aB3xZ9"*10),
                "POSTGRES_PASSWORD":"example-password-not-live",
                "DJANGO_ALLOWED_HOSTS":"sirago.example.com",
                "DJANGO_CSRF_TRUSTED_ORIGINS":"https://sirago.example.com"}
    def test_secure_defaults(self):
        s=production_settings(self.env())
        self.assertFalse(s["DEBUG"])
        self.assertFalse(s["SIRAGO_ENABLE_SIMULATED_PAYMENTS"])
        self.assertTrue(s["SESSION_COOKIE_SECURE"])
        self.assertTrue(s["CSRF_COOKIE_SECURE"])
        self.assertTrue(s["SECURE_SSL_REDIRECT"])
        self.assertEqual(s["X_FRAME_OPTIONS"],"DENY")
        self.assertGreater(s["SECURE_HSTS_SECONDS"],0)
        self.assertIsNone(s["SECURE_PROXY_SSL_HEADER"])
    def test_rejects_unsafe_configuration(self):
        for key,value in [
            ("DJANGO_DEBUG","1"),("SIRAGO_ENABLE_SIMULATED_PAYMENTS","1"),
            ("DJANGO_SECRET_KEY","local-dev-only"),("POSTGRES_PASSWORD","local_dev_only_change_me"),
            ("DJANGO_ALLOWED_HOSTS","*"),("DJANGO_ALLOWED_HOSTS",""),
            ("DJANGO_CSRF_TRUSTED_ORIGINS","http://sirago.example.com"),
            ("DJANGO_CSRF_TRUSTED_ORIGINS","https://other.example.com"),
            ("DJANGO_CSRF_TRUSTED_ORIGINS","https://sirago.example.com/path"),
        ]:
            with self.subTest(key=key,value=value):
                with self.assertRaises(ImproperlyConfigured):
                    production_settings({**self.env(),key:value})
    def test_explicit_proxy_trust(self):
        s=production_settings({**self.env(),"DJANGO_TRUST_HTTPS_PROXY":"1"})
        self.assertEqual(s["SECURE_PROXY_SSL_HEADER"],("HTTP_X_FORWARDED_PROTO","https"))
    @override_settings(DEBUG=False,SIRAGO_ENABLE_SIMULATED_PAYMENTS=True)
    def test_simulation_disabled_without_debug(self):
        self.assertFalse(simulation_enabled())
