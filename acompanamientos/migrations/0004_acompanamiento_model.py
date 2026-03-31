from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("acompanamientos", "0003_hitos_capacitacion_sincronica_y_fch"),
        ("admisiones", "0057_alter_archivoadmision_managers_and_more"),
    ]

    operations = [
        # 1. Crear tabla Acompanamiento
        migrations.CreateModel(
            name="Acompanamiento",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "nro_convenio",
                    models.CharField(blank=True, default="", max_length=100),
                ),
                ("fecha_creacion", models.DateTimeField(auto_now_add=True)),
                (
                    "admision",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="acompanamiento",
                        to="admisiones.admision",
                    ),
                ),
            ],
        ),
        # 2. InformacionRelevante: reemplazar comedor por acompanamiento
        # (0 registros en producción — migración segura sin data migration)
        migrations.RemoveField(
            model_name="informacionrelevante",
            name="comedor",
        ),
        migrations.AddField(
            model_name="informacionrelevante",
            name="acompanamiento",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="informacion_relevante",
                to="acompanamientos.acompanamiento",
                # temporal para pasar la migración; se elimina en la siguiente
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="informacionrelevante",
            name="acompanamiento",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="informacion_relevante",
                to="acompanamientos.acompanamiento",
            ),
        ),
        # 3. Prestacion: reemplazar comedor por acompanamiento
        # (0 registros en producción — migración segura sin data migration)
        migrations.RemoveField(
            model_name="prestacion",
            name="comedor",
        ),
        migrations.AddField(
            model_name="prestacion",
            name="acompanamiento",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="prestaciones",
                to="acompanamientos.acompanamiento",
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="prestacion",
            name="acompanamiento",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="prestaciones",
                to="acompanamientos.acompanamiento",
            ),
        ),
        # 4. Hitos: agregar acompanamiento nullable (comedor se mantiene por ahora)
        migrations.AddField(
            model_name="hitos",
            name="acompanamiento",
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="hitos",
                to="acompanamientos.acompanamiento",
            ),
        ),
    ]
