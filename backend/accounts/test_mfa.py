import time
from datetime import timedelta
from io import StringIO
from unittest.mock import patch

import pyotp
from django.core.cache import cache
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import Client, TestCase, override_settings
from django.utils import timezone

from .mfa import PENDING, VERIFIED, cipher
from .models import AdminMFA, AdminMFAEvent, User


@override_settings(SIRAGO_ADMIN_MFA_REQUIRED=True)
class AdminMFATests(TestCase):
    def setUp(self):
        cache.clear()
        self.addCleanup(cache.clear)
        self.password = "Mfa-Test-Only!26"
        self.user = User.objects.create_superuser(username="mfa-admin", password=self.password)
        self.now = int(time.time())
        self.clock = patch("accounts.mfa.time.time", return_value=self.now)
        self.clock.start()
        self.addCleanup(self.clock.stop)

    def post(self, route, values, client=None, **headers):
        return (client or self.client).post("/api/v1/auth/" + route + "/", values,
                                            content_type="application/json", **headers)

    def issue(self, reset=False):
        out = StringIO()
        call_command("admin_mfa_activation", self.user.username, reset=reset, stdout=out)
        return out.getvalue().strip().splitlines()[-1]

    def start(self, client=None):
        return self.post("login", {"identifier": self.user.username, "password": self.password}, client)

    def code(self, secret, offset=0):
        return pyotp.TOTP(secret).generate_otp(self.now // 30 + offset)

    def activate(self, client=None):
        client = client or self.client
        token = self.issue()
        self.assertEqual(self.start(client).json(), {"mfa_required": True, "stage": "enroll"})
        response = self.post("mfa/enroll", {"activation_code": token}, client)
        self.assertEqual(response.status_code, 200)
        setup = response.json()
        self.assertTrue(setup["qr"].startswith("data:image/png;base64,"))
        response = self.post("mfa/verify", {"code": self.code(setup["secret"])}, client)
        self.assertEqual(response.status_code, 200)
        return setup["secret"], response.json()["recovery_codes"]

    def test_password_only_has_no_privileged_session(self):
        self.assertEqual(self.start().status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)
        for url in ("me/", "supervision/", "supervision/finances/", "notifications/"):
            self.assertEqual(self.client.get("/api/v1/auth/" + url).status_code, 401)
        self.assertEqual(self.post("supervision/password", {}).status_code, 401)
        self.assertEqual(self.client.get("/admin/").status_code, 404)
        self.assertEqual(self.client.post("/admin/login/", {"username": self.user.username,
                         "password": self.password}).status_code, 404)

    def test_enrollment_requires_operator_code_and_password(self):
        token = self.issue()
        self.assertEqual(self.post("mfa/enroll", {"activation_code": token}).status_code, 401)
        self.start()
        self.assertEqual(self.post("mfa/enroll", {"activation_code": "0"*48}).status_code, 400)
        self.assertEqual(self.post("mfa/verify", {"code": "123456"}).status_code, 400)
        self.assertFalse(AdminMFA.objects.get(user=self.user).enabled)

    def test_enrollment_encrypts_secret_and_hashes_recovery_codes(self):
        secret, codes = self.activate()
        state = AdminMFA.objects.get(user=self.user)
        self.assertTrue(state.enabled)
        self.assertNotEqual(state.encrypted_secret, secret)
        self.assertEqual(cipher().decrypt(state.encrypted_secret.encode()).decode(), secret)
        self.assertEqual(len(codes), 8)
        self.assertEqual(len(set(codes)), 8)
        self.assertTrue(all(code not in state.recovery_hashes for code in codes))
        self.assertEqual(state.enrollment_hash, "")
        self.assertNotIn(PENDING, self.client.session)
        self.assertEqual(self.client.session[VERIFIED], str(state.version))
        self.assertEqual(self.client.get("/api/v1/auth/supervision/").status_code, 200)
        self.assertEqual(self.client.get("/api/v1/auth/me/").json()["role"], "ADMIN")
        self.assertTrue(AdminMFAEvent.objects.filter(user=self.user, kind="ENROLLMENT_CONFIRMED").exists())
        with self.assertRaises(CommandError):
            self.issue()

    def test_replay_and_next_totp(self):
        secret, _ = self.activate()
        self.post("logout", {})
        self.assertEqual(self.start().json()["stage"], "verify")
        self.assertEqual(self.post("mfa/verify", {"code": self.code(secret)}).status_code, 400)
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(self.post("mfa/verify", {"code": self.code(secret, 1)}).status_code, 200)
        self.post("logout", {})
        self.start()
        self.assertEqual(self.post("mfa/verify", {"code": self.code(secret, 1)}).status_code, 400)

    def test_recovery_code_only_once(self):
        _, codes = self.activate()
        self.post("logout", {})
        self.start()
        result = self.post("mfa/verify", {"code": codes[0]})
        self.assertEqual(result.status_code, 200)
        self.assertNotIn("recovery_codes", result.json())
        self.post("logout", {})
        self.start()
        self.assertEqual(self.post("mfa/verify", {"code": codes[0]}).status_code, 400)
        self.assertEqual(len(AdminMFA.objects.get(user=self.user).recovery_hashes), 7)

    def test_expired_challenge_and_token(self):
        token = self.issue()
        self.start()
        session = self.client.session
        p = session[PENDING]
        p["expires"] = self.now - 1
        session[PENDING] = p
        session.save()
        self.assertEqual(self.post("mfa/enroll", {"activation_code": token}).status_code, 401)
        AdminMFA.objects.filter(user=self.user).update(enrollment_expires=timezone.now()-timedelta(seconds=1))
        self.start()
        self.assertEqual(self.post("mfa/enroll", {"activation_code": token}).status_code, 400)

    def test_account_rate_limit_applies_across_ips(self):
        self.issue()
        self.start()
        for n in range(8):
            self.assertEqual(self.post("mfa/enroll", {"activation_code": "0"*48},
                                      REMOTE_ADDR="192.0.2."+str(n+1)).status_code, 400)
        self.assertEqual(self.post("mfa/enroll", {"activation_code": "0"*48},
                                  REMOTE_ADDR="192.0.2.99").status_code, 429)

    def test_old_session_and_reset_are_revoked(self):
        legacy = Client()
        legacy.force_login(self.user)
        self.assertEqual(legacy.get("/api/v1/auth/supervision/").status_code, 401)
        self.activate()
        self.issue(reset=True)
        self.assertEqual(self.client.get("/api/v1/auth/supervision/").status_code, 401)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_password_change_invalidates_pending_challenge(self):
        token = self.issue()
        self.start()
        self.user.set_password("Another-Mfa-Test-Only!26")
        self.user.save(update_fields=["password"])
        self.assertEqual(self.post("mfa/enroll", {"activation_code": token}).status_code, 401)

    def test_logout_cancels_pending_challenge(self):
        token = self.issue()
        self.start()
        self.post("logout", {})
        self.assertEqual(self.post("mfa/enroll", {"activation_code": token}).status_code, 401)

    def test_csrf_required_for_second_factor(self):
        client = Client(enforce_csrf_checks=True)
        client.get("/api/v1/auth/csrf/")
        token = client.cookies["csrftoken"].value
        self.assertEqual(self.post("login", {"identifier": self.user.username, "password": self.password},
                                   client, HTTP_X_CSRFTOKEN=token).status_code, 200)
        self.assertEqual(self.post("mfa/verify", {"code": "123456"}, client).status_code, 403)
        self.assertEqual(self.post("mfa/enroll", {"activation_code": "0"*48}, client).status_code, 403)

    def test_traveler_and_company_keep_normal_login(self):
        for role, phone in ((User.Role.TRAVELER, "+22370000011"), (User.Role.COMPANY, "+22370000012")):
            User.objects.create_user(username=role, role=role, phone=phone, password=self.password)
            response = self.post("login", {"identifier": phone, "password": self.password})
            self.assertEqual(response.json()["role"], role)
            self.assertIn("_auth_user_id", self.client.session)
            self.assertEqual(self.client.get("/api/v1/auth/supervision/").status_code, 403)
            self.post("logout", {})


    def test_authenticated_superadmin_search_treats_sql_syntax_as_text(self):
        from .models import Company
        owner = User.objects.create_user(username="security-mfa-company", role=User.Role.COMPANY)
        Company.objects.create(owner=owner,name="Security company",city="Bamako",address="Gare")
        self.activate()
        url = "/api/v1/auth/supervision/companies/"
        self.assertEqual(self.client.get(url).json()["total"],1)
        for value in ("' OR '1'='1", "%' OR 1=1 --", "x'; SELECT 1; --"):
            response = self.client.get(url,{"q":value})
            self.assertEqual(response.status_code,200,response.content)
            self.assertEqual(response.json()["items"],[])
        self.assertEqual(Company.objects.count(),1)
