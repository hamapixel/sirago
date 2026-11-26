from django.db import migrations,models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies=[("fleet","0007_test_boarding")]
    operations=[
        migrations.AlterField(model_name="booking",name="status",field=models.CharField(choices=[("HELD","En attente de paiement"),("TEST_PAID","Paiement simulé"),("REPORTED","Reportée"),("CANCELLED","Annulée")],default="HELD",max_length=16)),
        migrations.CreateModel(name="TestTicketReport",fields=[
            ("id",models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name="ID")),
            ("previous_amount",models.PositiveIntegerField()),
            ("new_amount",models.PositiveIntegerField()),
            ("created_at",models.DateTimeField(auto_now_add=True)),
            ("original",models.OneToOneField(on_delete=django.db.models.deletion.PROTECT,related_name="outgoing_report",to="fleet.booking")),
            ("replacement",models.OneToOneField(on_delete=django.db.models.deletion.PROTECT,related_name="incoming_report",to="fleet.booking")),
        ]),
    ]
