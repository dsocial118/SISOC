from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ciudadanos", "0024_ciudadano_revision_identidad_permission"),
    ]

    operations = [
        migrations.AlterField(
            model_name="ciudadano",
            name="fecha_nacimiento",
            field=models.DateField(blank=True, null=True),
        ),
    ]
