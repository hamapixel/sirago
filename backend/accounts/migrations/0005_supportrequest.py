from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies=[("accounts","0004_notification")]
    operations=[
        migrations.CreateModel(name="SupportRequest",fields=[
            ("id",models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name="ID")),
            ("reference",models.UUIDField(editable=False,unique=True)),
            ("category",models.CharField(choices=[("BOOKING","Réservation et billet"),("REPORT","Report de voyage"),("PAYMENT","Paiement"),("ACCOUNT","Compte et accès"),("TECHNICAL","Problème technique"),("OTHER","Autre")],max_length=16)),
            ("subject",models.CharField(max_length=120)),
            ("message",models.TextField(max_length=2000)),
            ("status",models.CharField(choices=[("OPEN","Reçue"),("IN_PROGRESS","En cours"),("RESOLVED","Résolue")],default="OPEN",max_length=16)),
            ("reply",models.TextField(blank=True,max_length=4000)),
            ("created_at",models.DateTimeField(auto_now_add=True)),
            ("updated_at",models.DateTimeField(auto_now=True)),
            ("requester",models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,related_name="support_requests",to=settings.AUTH_USER_MODEL)),
        ],options={"indexes":[models.Index(fields=["requester","-id"],name="support_requester_recent")]}),
    ]
