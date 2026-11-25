from django.db import migrations, models
from django.db.models import Q, F

class Migration(migrations.Migration):
    dependencies=[("fleet","0005_simulated_payment")]
    operations=[
        migrations.AddField(model_name="booking",name="ticket_mode",field=models.CharField(choices=[("group","Collectifs"),("individual","Individuels")],default="individual",max_length=10)),
        migrations.AlterField(model_name="booking",name="ticket_mode",field=models.CharField(choices=[("group","Collectifs"),("individual","Individuels")],default="group",max_length=10)),
        migrations.AddConstraint(model_name="booking",constraint=models.CheckConstraint(condition=Q(ticket_mode__in=["group","individual"]),name="fleet_booking_ticket_mode")),
        migrations.RemoveConstraint(model_name="booking",name="fleet_booking_passengers"),
        migrations.AddConstraint(model_name="booking",constraint=models.CheckConstraint(condition=Q(passengers__gte=1,passengers__lte=100),name="fleet_booking_passengers")),
        migrations.RemoveConstraint(model_name="bookingleg",name="fleet_leg_premium_values"),
        migrations.AddConstraint(model_name="bookingleg",constraint=models.CheckConstraint(condition=Q(premium_count__lte=100) & (Q(premium_count=0,premium_unit_price=0) | Q(premium_count__gt=0,premium_unit_price__gte=F("unit_price"),premium_unit_price__lte=1000000)),name="fleet_leg_premium_values")),
    ]
