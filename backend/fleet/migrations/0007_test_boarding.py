from uuid import uuid5
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

def backfill(apps,schema_editor):
    Leg=apps.get_model("fleet","BookingLeg")
    Ref=apps.get_model("fleet","TestTicketReference")
    db=schema_editor.connection.alias
    for l in Leg.objects.using(db).filter(booking__status="TEST_PAID",booking__simulated_payment__isnull=False).select_related("booking").iterator():
        b=l.booking
        premium=set(l.premium_positions)
        groups=[[i] for i in range(b.passengers)] if b.ticket_mode=="individual" else [g for g in ([i for i in range(b.passengers) if i not in premium],[i for i in range(b.passengers) if i in premium]) if g]
        for g in groups:
            suffix=str(g[0]) if len(g)==1 else "group:"+",".join(map(str,g))
            Ref.objects.using(db).create(leg_id=l.pk,anchor=g[0],code="SRG-TEST-"+uuid5(b.request_id,f"{b.pk}:{l.pk}:{suffix}").hex.upper())

class Migration(migrations.Migration):
    dependencies=[("fleet","0006_booking_ticket_mode"),migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations=[
        migrations.CreateModel(name="TestTicketReference",fields=[
            ("id",models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name="ID")),
            ("code",models.CharField(max_length=41,unique=True)),
            ("anchor",models.PositiveSmallIntegerField()),
            ("leg",models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,related_name="test_ticket_refs",to="fleet.bookingleg")),
        ],options={"constraints":[models.UniqueConstraint(fields=("leg","anchor"),name="fleet_test_ticket_anchor")]}),
        migrations.CreateModel(name="TestBoarding",fields=[
            ("id",models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name="ID")),
            ("passenger",models.PositiveSmallIntegerField()),
            ("boarded_at",models.DateTimeField(auto_now_add=True)),
            ("actor",models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,to=settings.AUTH_USER_MODEL)),
            ("leg",models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,related_name="test_boardings",to="fleet.bookingleg")),
        ],options={"constraints":[models.UniqueConstraint(fields=("leg","passenger"),name="fleet_test_boarding_once")]}),
        migrations.RunPython(backfill,migrations.RunPython.noop),
    ]
