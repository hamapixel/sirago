from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [("accounts", "0009_admin_mfa")]
    operations = [
        migrations.AddField(model_name="user", name="session_version",
                            field=models.PositiveBigIntegerField(default=0, editable=False)),
        migrations.CreateModel(name="AdminAction", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("target_type", models.CharField(max_length=16)),
            ("target_id", models.PositiveBigIntegerField()),
            ("before", models.CharField(max_length=32)),
            ("after", models.CharField(max_length=32)),
            ("reason", models.CharField(max_length=300)),
            ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
            ("actor", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="admin_actions", to="accounts.user")),
        ]),
    ]
