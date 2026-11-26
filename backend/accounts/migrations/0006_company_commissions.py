from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [("accounts", "0005_supportrequest")]
    operations = [
        migrations.CreateModel(name="CompanyCommission", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("rate_bps", models.PositiveSmallIntegerField()),
            ("updated_at", models.DateTimeField(auto_now=True)),
            ("company", models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name="commission_policy", to="accounts.company")),
        ], options={"constraints":[models.CheckConstraint(condition=models.Q(rate_bps__lte=1000),name="commission_rate_max_10")]}),
        migrations.CreateModel(name="CommissionChange", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("previous_bps", models.PositiveSmallIntegerField(null=True)),
            ("new_bps", models.PositiveSmallIntegerField()),
            ("created_at", models.DateTimeField(auto_now_add=True)),
            ("actor", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,to="accounts.user")),
            ("company", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,related_name="commission_changes",to="accounts.company")),
        ],options={"constraints":[models.CheckConstraint(condition=models.Q(new_bps__lte=1000),name="commission_change_new_max_10"),models.CheckConstraint(condition=models.Q(previous_bps__isnull=True)|models.Q(previous_bps__lte=1000),name="commission_change_old_max_10")]}),
    ]
