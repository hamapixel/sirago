from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies=[("fleet","0011_sandbox_receipts"),("accounts","0006_company_commissions")]
    operations=[migrations.CreateModel(name="SandboxCommission",fields=[
        ("id",models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name="ID")),
        ("gross",models.PositiveIntegerField()),
        ("rate_bps",models.PositiveSmallIntegerField(null=True)),
        ("commission",models.PositiveIntegerField(null=True)),
        ("company_share",models.PositiveIntegerField(null=True)),
        ("checkout",models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,related_name="commission_lines",to="fleet.sandboxcheckout")),
        ("leg",models.OneToOneField(on_delete=django.db.models.deletion.PROTECT,related_name="sandbox_commission",to="fleet.bookingleg")),
        ("company",models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,to="accounts.company")),
    ],options={"constraints":[
        models.CheckConstraint(condition=models.Q(gross__gt=0),name="sandbox_commission_gross_positive"),
        models.CheckConstraint(condition=models.Q(rate_bps__isnull=True,commission__isnull=True,company_share__isnull=True)|models.Q(rate_bps__isnull=False,rate_bps__lte=1000,commission__isnull=False,company_share__isnull=False,gross=models.F("commission")+models.F("company_share")),name="sandbox_commission_balanced"),
    ]})]
