from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [("fleet", "0004_premium_categories")]
    operations = [
        migrations.AlterField(model_name="booking",name="status",field=models.CharField(choices=[("HELD","En attente de paiement"),("TEST_PAID","Paiement simulé"),("CANCELLED","Annulée")],default="HELD",max_length=16)),
        migrations.CreateModel(name="SimulatedPayment",fields=[
            ("id",models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name="ID")),
            ("amount",models.PositiveIntegerField()),
            ("network",models.CharField(choices=[("orange_ml","Orange Money"),("moov_ml","Moov Money")],max_length=20)),
            ("created_at",models.DateTimeField(auto_now_add=True)),
            ("booking",models.OneToOneField(on_delete=django.db.models.deletion.PROTECT,related_name="simulated_payment",to="fleet.booking")),
        ]),
    ]
