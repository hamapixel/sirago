from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [("fleet", "0013_sandbox_settlement")]
    operations = [
        migrations.AddField(model_name="bus", name="driver_first_name", field=models.CharField(blank=True, default="", max_length=100)),
        migrations.AddField(model_name="bus", name="driver_last_name", field=models.CharField(blank=True, default="", max_length=100)),
        migrations.AddField(model_name="bus", name="driver_phone", field=models.CharField(blank=True, default="", max_length=20)),
    ]
