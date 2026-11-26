from django.conf import settings
from django.db import migrations,models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies=[("accounts","0003_companyagent")]
    operations=[
        migrations.CreateModel(name="Notification",fields=[
            ("id",models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name="ID")),
            ("kind",models.CharField(max_length=32)),
            ("title",models.CharField(max_length=120)),
            ("message",models.CharField(max_length=500)),
            ("created_at",models.DateTimeField(auto_now_add=True)),
            ("read_at",models.DateTimeField(blank=True,null=True)),
            ("recipient",models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,related_name="sirago_notifications",to=settings.AUTH_USER_MODEL)),
        ],options={"indexes":[models.Index(fields=["recipient","-id"],name="notif_recipient_recent"),models.Index(fields=["recipient","read_at"],name="notif_recipient_read")]}),
    ]
