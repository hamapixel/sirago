from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("accounts", "0010_admin_actions")]
    operations = [
        migrations.AddField(model_name="notification", name="booking_id",
                            field=models.PositiveBigIntegerField(null=True, blank=True)),
    ]
