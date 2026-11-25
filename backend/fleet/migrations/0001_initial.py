import django.db.models.deletion
from django.db import migrations, models

class Migration(migrations.Migration):
    initial = True
    dependencies = [("accounts","0002_company_email_constraint")]
    operations = [
        migrations.CreateModel(name="Bus", fields=[
            ("id",models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name="ID")),
            ("name",models.CharField(max_length=100)),
            ("plate",models.CharField(max_length=40)),
            ("capacity",models.PositiveIntegerField()),
            ("active",models.BooleanField(default=True)),
            ("company",models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,related_name="buses",to="accounts.company")),
        ], options={"constraints":[models.UniqueConstraint(fields=("company","plate"),name="fleet_unique_company_plate"),models.CheckConstraint(condition=models.Q(capacity__gte=1,capacity__lte=100),name="fleet_bus_capacity")]}),
        migrations.CreateModel(name="Route", fields=[
            ("id",models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name="ID")),
            ("origin",models.CharField(max_length=100)),
            ("destination",models.CharField(max_length=100)),
            ("boarding_point",models.CharField(max_length=200)),
            ("arrival_point",models.CharField(max_length=200)),
            ("duration_minutes",models.PositiveIntegerField()),
            ("price",models.PositiveIntegerField()),
            ("active",models.BooleanField(default=True)),
            ("company",models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,related_name="routes",to="accounts.company")),
        ], options={"constraints":[models.CheckConstraint(condition=~models.Q(origin=models.F("destination")),name="fleet_route_distinct_cities"),models.CheckConstraint(condition=models.Q(price__gte=1,price__lte=1000000,duration_minutes__gte=1,duration_minutes__lte=2880),name="fleet_route_values")]}),
        migrations.CreateModel(name="Departure",fields=[
            ("id",models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name="ID")),
            ("starts_at",models.DateTimeField()),
            ("ends_at",models.DateTimeField()),
            ("price",models.PositiveIntegerField()),
            ("capacity",models.PositiveIntegerField()),
            ("status",models.CharField(choices=[("DRAFT","Brouillon"),("PUBLISHED","Publié"),("SUSPENDED","Suspendu"),("CANCELLED","Annulé")],default="DRAFT",max_length=16)),
            ("company",models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,related_name="departures",to="accounts.company")),
            ("bus",models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,related_name="departures",to="fleet.bus")),
            ("route",models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,related_name="departures",to="fleet.route")),
        ],options={"constraints":[models.CheckConstraint(condition=models.Q(ends_at__gt=models.F("starts_at")),name="fleet_departure_interval"),models.CheckConstraint(condition=models.Q(capacity__gte=1,capacity__lte=100,price__gte=1,price__lte=1000000),name="fleet_departure_values")],"indexes":[models.Index(fields=["company","starts_at"],name="fleet_company_start_idx"),models.Index(fields=["bus","starts_at"],name="fleet_bus_start_idx")]}),
    ]
