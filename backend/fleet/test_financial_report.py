from datetime import timedelta
from io import BytesIO
from uuid import uuid4
from django.test import TestCase, override_settings
from accounts.test_helpers import force_mfa_login
from django.utils import timezone
from openpyxl import load_workbook
from accounts.models import CompanyCommission, User
from .models import Booking, SandboxCheckout, SandboxSettlement, SimulatedPayment
from .test_booking import BookingFixture
from .commissions import freeze_commissions
from zoneinfo import ZoneInfo

@override_settings(SIRAGO_ADMIN_MFA_REQUIRED=True)
class FinancialReportTests(BookingFixture,TestCase):
    def setUp(self):
        super().setUp()
        self.admin=User.objects.create_superuser(username="financial-admin",password="test-password")
        self.client.force_login(self.user)
        r=self.reserve()
        self.assertEqual(r.status_code,201,r.content)
        self.booking=Booking.objects.get(pk=r.json()["id"])
        CompanyCommission.objects.create(company=self.company,rate_bps=500)
        self.checkout=SandboxCheckout.objects.create(booking=self.booking,amount=16000,status="PAID",provider_id=uuid4(),transaction_id=uuid4(),issued_at=timezone.now())
        freeze_commissions(self.checkout,list(self.booking.legs.all()))
        self.booking.status=Booking.Status.TEST_PAID
        self.booking.save(update_fields=["status"])
        self.settlement=SandboxSettlement.objects.create(company=self.company,actor=self.admin,reference=uuid4(),amount=5000)
        self.day=timezone.now().astimezone(ZoneInfo("Africa/Bamako")).date().isoformat()
        self.params={"date_from":self.day,"date_to":self.day}
        self.base="/api/v1/auth/supervision/finances/"
        force_mfa_login(self.client, self.admin)
    def report(self,**params):
        r=self.client.get(self.base,{**self.params,**params})
        self.assertEqual(r.status_code,200,r.content)
        return r.json()
    def test_summary_and_histories(self):
        d=self.report()
        self.assertEqual(d["summary"],{"sandbox":16000,"local":0,"commission":800,"share":15200,"unallocated":0,"settled":5000,"real":0})
        self.assertFalse(d["real_payments_enabled"])
        self.assertEqual(d["total"],1)
        self.assertEqual(d["items"][0]["sandbox"],16000)
        self.assertEqual(self.report(view="commissions")["items"][0]["rate_bps"],500)
        self.assertEqual(self.report(view="settlements")["items"][0]["amount"],5000)
        self.assertEqual(self.report(q="nonexistent")["summary"]["sandbox"],0)
    def test_unallocated_and_pending(self):
        self.checkout.commission_lines.update(rate_bps=None,commission=None,company_share=None)
        d=self.report()
        self.assertEqual(d["summary"]["unallocated"],16000)
        self.assertEqual(d["summary"]["commission"],0)
        self.checkout.status="PENDING"
        self.checkout.save(update_fields=["status"])
        self.assertEqual(self.report()["summary"]["sandbox"],0)
    def test_no_historical_recalculation_and_period(self):
        self.checkout.commission_lines.all().delete()
        self.assertEqual(self.report()["summary"]["unallocated"],16000)
        self.assertEqual(self.report(view="commissions")["total"],0)
        SandboxSettlement.objects.filter(pk=self.settlement.pk).update(created_at=timezone.now()-timedelta(days=2))
        self.assertEqual(self.report()["summary"]["settled"],0)
        self.assertEqual(self.report(date_from="2000-01-01",date_to="2000-01-01")["total"],0)
    def test_local_simulation_separate(self):
        self.checkout.commission_lines.all().delete()
        self.checkout.delete()
        SimulatedPayment.objects.create(booking=self.booking,amount=16000,network="orange_ml")
        d=self.report()["summary"]
        self.assertEqual((d["local"],d["sandbox"],d["commission"],d["real"]),(16000,0,0,0))
    def test_permissions_and_validation(self):
        for params in ({"date_from":"bad"},{"date_from":"2020-01-01","date_to":"2026-01-01"},{"view":"unknown"},{"page_size":"3"}):
            self.assertEqual(self.client.get(self.base,params).status_code,400)
        self.client.force_login(self.owner)
        for path in ("","pdf/","excel/"):
            self.assertEqual(self.client.get(self.base+path,self.params).status_code,403)
        self.client.logout()
        self.assertEqual(self.client.get(self.base,self.params).status_code,401)
    def test_exports_and_literal_text(self):
        self.company.name="=1+1"
        self.company.save(update_fields=["name"])
        pdf=self.client.get(self.base+"pdf/",self.params)
        self.assertEqual(pdf.status_code,200,pdf.content[:100])
        self.assertTrue(pdf.content.startswith(b"%PDF"))
        xlsx=self.client.get(self.base+"excel/",self.params)
        self.assertEqual(xlsx.status_code,200,xlsx.content[:100])
        wb=load_workbook(BytesIO(xlsx.content))
        self.assertEqual(wb.sheetnames,["Synthèse","Compagnies","Commissions","Reversements"])
        self.assertEqual(wb["Compagnies"]["A4"].value,"=1+1")
        self.assertEqual(wb["Compagnies"]["A4"].data_type,"s")
        self.assertEqual(wb["Compagnies"]["C4"].value,16000)
        self.assertEqual(wb["Reversements"]["D4"].value,5000)
