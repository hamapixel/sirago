from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies=[("fleet","0008_test_ticket_report")]
    operations=[
        migrations.AddField(model_name="testticketreport",name="retained",field=models.OneToOneField(blank=True,null=True,on_delete=django.db.models.deletion.PROTECT,related_name="retained_report",to="fleet.booking")),
        migrations.AddField(model_name="testticketreport",name="selected_positions",field=models.JSONField(blank=True,default=list)),
    ]
