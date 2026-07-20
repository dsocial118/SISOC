from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("comedores", "0048_issue_2063_convenio_abordaje")]

    operations = [
        migrations.AddField(
            model_name="prestacionalimentariaconformidad",
            name="certificacion_pdf",
            field=models.FileField(
                blank=True,
                null=True,
                upload_to="comedores/certificaciones_prestaciones/",
            ),
        ),
    ]
