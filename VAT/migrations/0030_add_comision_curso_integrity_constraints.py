from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("VAT", "0029_planversioncurricular_provincia"),
    ]

    operations = [
        migrations.AddConstraint(
            model_name="comisionhorario",
            constraint=models.CheckConstraint(
                check=(
                    models.Q(comision__isnull=False, comision_curso__isnull=True)
                    | models.Q(comision__isnull=True, comision_curso__isnull=False)
                ),
                name="vat_comhor_xor_comision_refs",
            ),
        ),
        migrations.AddConstraint(
            model_name="comisionhorario",
            constraint=models.UniqueConstraint(
                fields=("comision_curso", "dia_semana", "hora_desde", "hora_hasta"),
                condition=models.Q(comision_curso__isnull=False),
                name="vat_comhor_comisioncurso_horario_uniq",
            ),
        ),
        migrations.AddConstraint(
            model_name="sesioncomision",
            constraint=models.CheckConstraint(
                check=(
                    models.Q(comision__isnull=False, comision_curso__isnull=True)
                    | models.Q(comision__isnull=True, comision_curso__isnull=False)
                ),
                name="vat_sesion_xor_comision_refs",
            ),
        ),
        migrations.AddConstraint(
            model_name="sesioncomision",
            constraint=models.UniqueConstraint(
                fields=("comision_curso", "horario", "fecha"),
                condition=models.Q(comision_curso__isnull=False),
                name="vat_sesion_comisioncurso_horario_fecha_uniq",
            ),
        ),
        migrations.AddConstraint(
            model_name="inscripcion",
            constraint=models.CheckConstraint(
                check=(
                    models.Q(comision__isnull=False, comision_curso__isnull=True)
                    | models.Q(comision__isnull=True, comision_curso__isnull=False)
                ),
                name="vat_inscripcion_xor_comision_refs",
            ),
        ),
        migrations.AddConstraint(
            model_name="inscripcion",
            constraint=models.UniqueConstraint(
                fields=("ciudadano", "comision_curso"),
                condition=models.Q(comision_curso__isnull=False),
                name="vat_inscripcion_ciudadano_comisioncurso_uniq",
            ),
        ),
    ]
