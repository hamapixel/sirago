from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("accounts", "0006_company_commissions")]
    operations = [
        migrations.AddField(model_name="company", name="logo", field=models.TextField(blank=True, default="", editable=False)),
        migrations.AddField(model_name="company", name="banner", field=models.TextField(blank=True, default="", editable=False)),
    ]
