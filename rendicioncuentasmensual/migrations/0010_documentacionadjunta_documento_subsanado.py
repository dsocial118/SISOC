from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        (
            "rendicioncuentasmensual",
            "0009_rendicioncuentamensual_usuario_ultima_modificacion",
        ),
    ]

    operations = [
        migrations.AddField(
            model_name="documentacionadjunta",
            name="documento_subsanado",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=models.SET_NULL,
                related_name="subsanaciones",
                to="rendicioncuentasmensual.documentacionadjunta",
                verbose_name="Documento subsanado",
            ),
        ),
    ]
