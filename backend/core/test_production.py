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
                "DJANGO_CSRF_TRUSTED_ORIGINS":"https://sirago.example.com",
                "SIRAGO_REDIS_URL":"redis://redis:6379/0"}
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
        cache = s["CACHES"]["default"]
        self.assertEqual(cache["BACKEND"], "django.core.cache.backends.redis.RedisCache")
        self.assertEqual(cache["LOCATION"], "redis://redis:6379/0")
        self.assertEqual(cache["OPTIONS"]["socket_timeout"], 2)
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
    def test_production_rejects_invalid_shared_cache(self):
        for url in ("", "locmem://", "http://redis:6379/0",
                    "redis://", "redis://redis:99999/0", "redis://redis/no-db",
                    "redis://redis:6379/0?option=1", "redis://redis:6379/0#fragment",
                    "redis://redis:6379/0\n"):
            with self.subTest(url=url):
                with self.assertRaises(ImproperlyConfigured):
                    production_settings({**self.env(), "SIRAGO_REDIS_URL": url})

    def test_cache_configuration_does_not_disclose_credentials_on_error(self):
        secret = "example-private-cache-password"
        with self.assertRaises(ImproperlyConfigured) as exc:
            production_settings({**self.env(), "SIRAGO_REDIS_URL":
                                 "http://:" + secret + "@redis:6379/0"})
        self.assertNotIn(secret, str(exc.exception))

    def test_tls_redis_url_is_accepted(self):
        url = "rediss://:example-password@redis.example.com:6380/1"
        s = production_settings({**self.env(), "SIRAGO_REDIS_URL": url})
        self.assertEqual(s["CACHES"]["default"]["LOCATION"], url)

    def test_production_rejects_sandbox_flags(self):
        for flag in ("SIRAGO_ENABLE_SASPAY_SANDBOX",
                     "SIRAGO_ENABLE_SASPAY_TICKETS", "SIRAGO_SASPAY_LOCAL_RETURN"):
            with self.subTest(flag=flag):
                with self.assertRaises(ImproperlyConfigured):
                    production_settings({**self.env(), flag: "1"})

    def test_explicit_proxy_trust(self):
        s=production_settings({**self.env(),"DJANGO_TRUST_HTTPS_PROXY":"1"})
        self.assertEqual(s["SECURE_PROXY_SSL_HEADER"],("HTTP_X_FORWARDED_PROTO","https"))
    @override_settings(DEBUG=False,SIRAGO_ENABLE_SIMULATED_PAYMENTS=True)
    def test_simulation_disabled_without_debug(self):
        self.assertFalse(simulation_enabled())
