from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.db.models.functions

class Migration(migrations.Migration):
    dependencies = [("accounts", "0001_initial")]
    operations = [
        migrations.AddConstraint(model_name="user", constraint=models.UniqueConstraint(django.db.models.functions.Lower("email"), condition=~models.Q(email=""), name="unique_nonempty_email_ci")),
        migrations.CreateModel(name="Company", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("name", models.CharField(max_length=150)),
            ("city", models.CharField(max_length=100)),
            ("address", models.CharField(max_length=250)),
            ("registration_number", models.CharField(blank=True, max_length=100)),
            ("status", models.CharField(choices=[("PENDING","En attente"),("VERIFIED","Validée"),("REJECTED","Rejetée"),("SUSPENDED","Suspendue")], default="PENDING", max_length=16)),
            ("created_at", models.DateTimeField(auto_now_add=True)),
            ("owner", models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name="company", to=settings.AUTH_USER_MODEL)),
        ]),
    ]
