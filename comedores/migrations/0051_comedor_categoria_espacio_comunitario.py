from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("comedores", "0050_merge_20260720_1400"),
    ]

    operations = [
        migrations.AddField(
            model_name="comedor",
            name="categoria_espacio_comunitario",
            field=models.CharField(
                blank=True,
                choices=[
                    ("asociacion_civil", "Asociación Civil"),
                    (
                        "asociacion_vecinal",
                        "Asociación Vecinal / Sociedad de Fomento",
                    ),
                    ("cooperativa_trabajo", "Cooperativa de Trabajo"),
                    ("fundacion", "Fundación"),
                    ("grupo_comunitario_base", "Grupo Comunitario de Base"),
                    ("centro_desarrollo_infantil", "Centro de Desarrollo Infantil"),
                    ("centro_jubilados", "Centro de Jubilados"),
                    ("club_social_deportivo", "Club Social y/o Deportivo"),
                    ("hogar", "Hogar"),
                    ("institucion_educativa", "Institución Educativa"),
                    ("institucion_religiosa", "Institución Religiosa"),
                    (
                        "movimiento_trabajadores_desocupados",
                        "Movimiento de Trabajadores Desocupados",
                    ),
                    (
                        "tecnicos_profesionales",
                        "Organización de Técnicos y Profesionales",
                    ),
                    ("otra", "Otra (especificar)"),
                ],
                max_length=50,
                null=True,
                verbose_name="Categorización de espacio comunitario",
            ),
        ),
        migrations.AddField(
            model_name="comedor",
            name="categoria_espacio_comunitario_otra",
            field=models.CharField(
                blank=True,
                max_length=255,
                null=True,
                verbose_name="Otra categorización de espacio comunitario",
            ),
        ),
    ]
