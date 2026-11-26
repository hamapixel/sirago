from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [("accounts", "0007_company_branding")]
    operations = [
        migrations.CreateModel(name="PushSubscription", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("session_key", models.CharField(max_length=40)),
            ("endpoint", models.URLField(max_length=2048, unique=True)),
            ("p256dh", models.CharField(max_length=100)),
            ("auth", models.CharField(max_length=40)),
            ("created_at", models.DateTimeField(auto_now_add=True)),
            ("recipient", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="accounts.user")),
        ]),
        migrations.CreateModel(name="PushDelivery", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("attempts", models.PositiveSmallIntegerField(default=0)),
            ("next_attempt", models.DateTimeField(db_index=True)),
            ("notification", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="accounts.notification")),
            ("subscription", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="accounts.pushsubscription")),
        ]),
        migrations.AddConstraint(model_name="pushdelivery", constraint=models.UniqueConstraint(fields=("subscription","notification"),name="push_unique_delivery")),
    ]
