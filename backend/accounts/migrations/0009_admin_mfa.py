import uuid
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [("accounts", "0008_web_push")]
    operations = [
        migrations.CreateModel(name="AdminMFA", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("enabled", models.BooleanField(default=False)),
            ("encrypted_secret", models.TextField(blank=True, default="")),
            ("enrollment_hash", models.CharField(max_length=64, blank=True, default="")),
            ("enrollment_expires", models.DateTimeField(blank=True, null=True)),
            ("last_step", models.BigIntegerField(default=-1)),
            ("recovery_hashes", models.JSONField(default=list)),
            ("version", models.UUIDField(default=uuid.uuid4, editable=False)),
            ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="admin_mfa", to="accounts.user")),
        ]),
        migrations.CreateModel(name="AdminMFAEvent", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("kind", models.CharField(max_length=32)),
            ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
            ("user", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to="accounts.user")),
        ]),
    ]
