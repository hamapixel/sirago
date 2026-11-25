from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [("fleet","0001_initial"),migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.CreateModel(name="Booking",fields=[
            ("id",models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name="ID")),
            ("request_id",models.UUIDField()),
            ("passengers",models.PositiveIntegerField()),
            ("status",models.CharField(choices=[("HELD","En attente de paiement"),("CANCELLED","Annulée")],default="HELD",max_length=16)),
            ("expires_at",models.DateTimeField()),
            ("created_at",models.DateTimeField(auto_now_add=True)),
            ("traveler",models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,related_name="bookings",to=settings.AUTH_USER_MODEL)),
        ],options={"constraints":[models.UniqueConstraint(fields=("traveler","request_id"),name="fleet_booking_request_unique"),models.CheckConstraint(condition=models.Q(passengers__gte=1,passengers__lte=10),name="fleet_booking_passengers")]}),
        migrations.CreateModel(name="BookingLeg",fields=[
            ("id",models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name="ID")),
            ("position",models.PositiveSmallIntegerField()),
            ("unit_price",models.PositiveIntegerField()),
            ("booking",models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,related_name="legs",to="fleet.booking")),
            ("departure",models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,related_name="booking_legs",to="fleet.departure")),
        ],options={"constraints":[models.UniqueConstraint(fields=("booking","position"),name="fleet_booking_leg_position"),models.UniqueConstraint(fields=("booking","departure"),name="fleet_booking_leg_unique"),models.CheckConstraint(condition=models.Q(position__lte=1,unit_price__gte=1,unit_price__lte=1000000),name="fleet_booking_leg_values")]}),
    ]
