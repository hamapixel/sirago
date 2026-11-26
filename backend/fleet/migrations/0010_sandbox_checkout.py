from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies=[("fleet","0009_partial_ticket_report")]
    operations=[migrations.CreateModel(name="SandboxCheckout",fields=[
        ("id",models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name="ID")),
        ("amount",models.PositiveIntegerField()),
        ("provider_id",models.UUIDField(blank=True,null=True,unique=True)),
        ("checkout_url",models.URLField(blank=True,max_length=1000)),
        ("status",models.CharField(default="CREATING",max_length=16)),
        ("created_at",models.DateTimeField(auto_now_add=True)),
        ("checked_at",models.DateTimeField(blank=True,null=True)),
        ("booking",models.OneToOneField(on_delete=django.db.models.deletion.PROTECT,related_name="sandbox_checkout",to="fleet.booking")),
    ])]
