from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies=[("fleet","0012_sandbox_commission")]
    operations=[migrations.CreateModel(name="SandboxSettlement",fields=[
        ("id",models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name="ID")),
        ("reference",models.UUIDField(unique=True)),
        ("amount",models.PositiveBigIntegerField()),
        ("created_at",models.DateTimeField(auto_now_add=True)),
        ("company",models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,related_name="sandbox_settlements",to="accounts.company")),
        ("actor",models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,to="accounts.user")),
    ],options={"constraints":[models.CheckConstraint(condition=models.Q(amount__gt=0),name="sandbox_settlement_positive")]})]
