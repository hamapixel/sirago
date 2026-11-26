from django.test import TestCase
class HealthTest(TestCase):
    def test_health(self):
        response = self.client.get("/api/v1/health/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")
    def test_health_get_only(self):
        self.assertEqual(self.client.post("/api/v1/health/").status_code,405)


from unittest.mock import patch
from django.test import RequestFactory, SimpleTestCase, override_settings
from core.views import health

@override_settings(DEBUG=False, CACHES={"default": {
    "BACKEND": "django.core.cache.backends.redis.RedisCache",
    "LOCATION": "redis://redis:6379/0",
}})
class ProductionHealthTest(SimpleTestCase):
    def setUp(self):
        self.request = RequestFactory().get("/api/v1/health/")

    @patch("core.views.cache")
    @patch("core.views.connection")
    def test_health_checks_database_and_shared_cache(self, db, cache):
        response = health(self.request)
        self.assertEqual(response.status_code, 200)
        db.cursor.return_value.__enter__.return_value.execute.assert_called_once_with("SELECT 1")
        cache.get.assert_called_once_with("sirago-health-probe")
        self.assertIn("no-store", response["Cache-Control"])

    @patch("core.views.cache")
    @patch("core.views.connection")
    def test_redis_failure_returns_503_without_details(self, db, cache):
        cache.get.side_effect = RuntimeError("private Redis credentials")
        response = health(self.request)
        self.assertEqual(response.status_code, 503)
        self.assertNotIn(b"credentials", response.content)

    @patch("core.views.cache")
    @patch("core.views.connection")
    def test_database_failure_returns_503_without_details(self, db, cache):
        db.cursor.side_effect = RuntimeError("private database credentials")
        response = health(self.request)
        self.assertEqual(response.status_code, 503)
        self.assertNotIn(b"credentials", response.content)
        cache.get.assert_not_called()
