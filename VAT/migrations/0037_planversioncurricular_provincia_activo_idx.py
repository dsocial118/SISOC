from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("VAT", "0036_alter_institucioncontacto_options_and_more"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="planversioncurricular",
            index=models.Index(
                fields=["provincia", "activo"],
                name="vat_plan_prov_act_idx",
            ),
        ),
    ]
