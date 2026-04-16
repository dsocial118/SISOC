from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("VAT", "0038_curso_prioritario"),
    ]

    operations = [
        migrations.AddField(
            model_name="comision",
            name="acepta_lista_espera",
            field=models.BooleanField(
                default=False,
                help_text=(
                    "Si está activo, cuando la comisión se quede sin cupos las "
                    "nuevas inscripciones pasan a espera."
                ),
                verbose_name="Acepta Lista de Espera",
            ),
        ),
        migrations.AddField(
            model_name="comisioncurso",
            name="acepta_lista_espera",
            field=models.BooleanField(
                default=False,
                help_text=(
                    "Si está activo, cuando la comisión se quede sin cupos las "
                    "nuevas inscripciones pasan a espera."
                ),
                verbose_name="Acepta Lista de Espera",
            ),
        ),
        migrations.AlterField(
            model_name="inscripcion",
            name="estado",
            field=models.CharField(
                choices=[
                    ("pre_inscripta", "Pre-inscripta"),
                    ("en_espera", "En Espera"),
                    ("inscripta", "Inscripta"),
                    ("validada_presencial", "Validada Presencial"),
                    ("completada", "Completada"),
                    ("abandonada", "Abandonada"),
                    ("rechazada", "Rechazada"),
                ],
                default="pre_inscripta",
                max_length=30,
                verbose_name="Estado",
            ),
        ),
    ]
