from django.test import TestCase
class HealthTest(TestCase):
    def test_health(self):
        response = self.client.get("/api/v1/health/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")
    def test_health_get_only(self):
        self.assertEqual(self.client.post("/api/v1/health/").status_code,405)
