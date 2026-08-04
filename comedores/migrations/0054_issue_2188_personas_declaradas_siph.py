from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("comedores", "0053_issue_1961_proyecto_organizacion"),
    ]

    operations = [
        migrations.AddField(
            model_name="comedordatosconveniopnud",
            name="personas_declaradas_siph",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
    ]
