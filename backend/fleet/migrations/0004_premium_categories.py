from django.db import migrations, models
from django.db.models import Q,F

class Migration(migrations.Migration):
    dependencies=[("fleet","0003_booking_passenger_names")]
    operations=[
        migrations.AddField(model_name="bus",name="premium_capacity",field=models.PositiveIntegerField(default=0)),
        migrations.AddConstraint(model_name="bus",constraint=models.CheckConstraint(condition=Q(premium_capacity__lt=F("capacity")),name="fleet_bus_premium_capacity")),
        migrations.AddField(model_name="departure",name="premium_capacity",field=models.PositiveIntegerField(default=0)),
        migrations.AddField(model_name="departure",name="premium_price",field=models.PositiveIntegerField(default=0)),
        migrations.AddConstraint(model_name="departure",constraint=models.CheckConstraint(condition=Q(premium_capacity__lt=F("capacity")) & (Q(premium_capacity=0,premium_price=0) | Q(premium_capacity__gt=0,premium_price__gte=F("price"),premium_price__lte=1000000)),name="fleet_departure_premium_values")),
        migrations.AddField(model_name="bookingleg",name="premium_count",field=models.PositiveIntegerField(default=0)),
        migrations.AddField(model_name="bookingleg",name="premium_unit_price",field=models.PositiveIntegerField(default=0)),
        migrations.AddField(model_name="bookingleg",name="premium_positions",field=models.JSONField(default=list,blank=True)),
        migrations.AddConstraint(model_name="bookingleg",constraint=models.CheckConstraint(condition=Q(premium_count__lte=10) & (Q(premium_count=0,premium_unit_price=0) | Q(premium_count__gt=0,premium_unit_price__gte=F("unit_price"),premium_unit_price__lte=1000000)),name="fleet_leg_premium_values")),
    ]
