from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("comedores", "0046_comedordatosconveniopnud_prestaciones"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="prestacionalimentariaconformidad",
            name="uniq_conformidad_prestacion_alimentaria_mes",
        ),
    ]
