from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [("fleet", "0002_booking_bookingleg")]
    operations = [
        migrations.AddField(model_name="booking", name="passenger_names", field=models.JSONField(blank=True, default=list)),
    ]
