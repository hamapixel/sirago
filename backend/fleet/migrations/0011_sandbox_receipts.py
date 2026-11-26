from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies=[("fleet","0010_sandbox_checkout")]
    operations=[
        migrations.AddField(model_name="sandboxcheckout",name="transaction_id",field=models.UUIDField(blank=True,null=True,unique=True)),
        migrations.AddField(model_name="sandboxcheckout",name="issued_at",field=models.DateTimeField(blank=True,null=True)),
        migrations.CreateModel(name="SandboxWebhookReceipt",fields=[
            ("id",models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name="ID")),
            ("transaction_id",models.UUIDField(unique=True)),
            ("received_at",models.DateTimeField(auto_now_add=True)),
            ("matched_at",models.DateTimeField(blank=True,null=True)),
        ]),
    ]
