from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings

class Migration(migrations.Migration):
    dependencies=[("accounts","0002_company_email_constraint")]
    operations=[
        migrations.CreateModel(name="CompanyAgent",fields=[
            ("id",models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name="ID")),
            ("role",models.CharField(choices=[("CLERK","Guichetier"),("CONTROLLER","Contrôleur")],max_length=16)),
            ("created_at",models.DateTimeField(auto_now_add=True)),
            ("company",models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,related_name="agents",to="accounts.company")),
            ("user",models.OneToOneField(on_delete=django.db.models.deletion.PROTECT,related_name="company_agent",to=settings.AUTH_USER_MODEL)),
        ],options={"constraints":[models.CheckConstraint(condition=models.Q(role__in=["CLERK","CONTROLLER"]),name="accounts_agent_role")]}),
    ]
