from django.db import migrations, models


CALENDARIO_CHOICES = [
    ("si", "Sí"),
    ("no", "No"),
    ("no_sabe", "No sabe"),
]
CALENDARIO_BOOLEANO_A_RESPUESTA = ((True, "si"), (False, "no"))


def migrar_calendario_a_respuesta(apps, schema_editor):
    nomina_model = apps.get_model("centrodeinfancia", "NominaCentroInfancia")
    for valor, respuesta in CALENDARIO_BOOLEANO_A_RESPUESTA:
        nomina_model.objects.filter(calendario_vacunacion_al_dia=valor).update(
            calendario_vacunacion_respuesta=respuesta
        )


def revertir_calendario_a_booleano(apps, schema_editor):
    nomina_model = apps.get_model("centrodeinfancia", "NominaCentroInfancia")
    for valor, respuesta in CALENDARIO_BOOLEANO_A_RESPUESTA:
        nomina_model.objects.filter(calendario_vacunacion_respuesta=respuesta).update(
            calendario_vacunacion_al_dia=valor
        )


class Migration(migrations.Migration):
    dependencies = [
        (
            "centrodeinfancia",
            "0047_alter_formulariocdi_realiza_acciones_acompanamiento_vulneracion_derechos_and_more",
        ),
    ]

    operations = [
        migrations.AddField(
            model_name="nominacentroinfancia",
            name="calendario_vacunacion_respuesta",
            field=models.CharField(
                blank=True,
                choices=CALENDARIO_CHOICES,
                max_length=8,
                null=True,
                verbose_name="Calendario de vacunación al día",
            ),
        ),
        migrations.RunPython(
            migrar_calendario_a_respuesta,
            revertir_calendario_a_booleano,
        ),
        migrations.RemoveField(
            model_name="nominacentroinfancia",
            name="calendario_vacunacion_al_dia",
        ),
        migrations.RenameField(
            model_name="nominacentroinfancia",
            old_name="calendario_vacunacion_respuesta",
            new_name="calendario_vacunacion_al_dia",
        ),
        migrations.AlterField(
            model_name="nominacentroinfancia",
            name="cobertura_salud",
            field=models.CharField(
                blank=True,
                choices=[
                    ("publica_exclusiva", "Pública exclusiva"),
                    ("obra_social", "Obra social"),
                    ("prepaga", "Prepaga / medicina privada"),
                    ("no_corresponde", "No corresponde"),
                    ("no_sabe", "No sabe"),
                ],
                max_length=32,
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="nominacentroinfancia",
            name="controles_sanitarios_ultimo_anio",
            field=models.CharField(
                blank=True,
                choices=[
                    ("0", "0 controles"),
                    ("1", "1 control"),
                    ("2", "2 controles"),
                    ("3", "3 controles"),
                    ("4", "4 controles"),
                    ("5", "5 controles"),
                    ("6", "6 controles"),
                    ("7", "7 controles"),
                    ("no_sabe", "No sabe"),
                ],
                max_length=8,
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="nominacentroinfancia",
            name="lactancia",
            field=models.CharField(
                blank=True,
                choices=[
                    ("exclusiva", "Exclusiva"),
                    ("complementaria", "Complementaria"),
                    ("continuada", "Continuada"),
                    ("no_lactante", "No es lactante"),
                    ("no_sabe", "No sabe"),
                ],
                max_length=16,
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="nominacentroinfancia",
            name="necesito_interprete",
            field=models.CharField(
                blank=True,
                choices=[
                    ("si", "Sí"),
                    ("no", "No"),
                    ("no_sabe", "No sabe"),
                ],
                max_length=8,
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="nominacentroinfancia",
            name="recibe_apoyo_desarrollo",
            field=models.CharField(
                blank=True,
                choices=[
                    ("si", "Sí"),
                    ("no", "No"),
                    ("no_sabe", "No sabe"),
                ],
                max_length=8,
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="trabajador",
            name="anos_trabajo_primera_infancia",
            field=models.CharField(
                blank=True,
                choices=[
                    ("1", "1"),
                    ("2", "2"),
                    ("3", "3"),
                    ("4", "4"),
                    ("5", "5"),
                    ("6", "6"),
                    ("7", "7"),
                    ("8", "8"),
                    ("9", "9"),
                    ("10_o_mas", "10 o más"),
                    ("no_sabe", "No sabe"),
                ],
                max_length=16,
                null=True,
                verbose_name="Años de trabajo en primera infancia",
            ),
        ),
        migrations.AlterField(
            model_name="trabajador",
            name="es_interprete",
            field=models.CharField(
                blank=True,
                choices=[
                    ("si", "Sí"),
                    ("no", "No"),
                    ("no_sabe", "No sabe"),
                ],
                max_length=16,
                null=True,
                verbose_name="¿Es intérprete?",
            ),
        ),
        migrations.AlterField(
            model_name="trabajador",
            name="nivel_educativo",
            field=models.CharField(
                blank=True,
                choices=[
                    ("nunca", "Nunca asistió a un establecimiento educativo"),
                    ("inicial_incompleto", "Inicial incompleto"),
                    ("inicial_en_curso", "Inicial en curso"),
                    ("inicial_completo", "Inicial completo"),
                    ("primario_incompleto", "Primario incompleto"),
                    ("primario_en_curso", "Primario en curso"),
                    ("primario_completo", "Primario completo"),
                    ("secundario_incompleto", "Secundario incompleto"),
                    ("secundario_en_curso", "Secundario en curso"),
                    ("secundario_completo", "Secundario completo"),
                    ("superior_incompleto", "Superior incompleto"),
                    ("superior_en_curso", "Superior en curso"),
                    ("superior_completo", "Superior completo"),
                    ("no_sabe", "No sabe"),
                ],
                max_length=32,
                null=True,
                verbose_name="Nivel educativo",
            ),
        ),
    ]
