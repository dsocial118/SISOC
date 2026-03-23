# Generated manually on 2026-03-22

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("VAT", "0013_remove_actividades"),
        ("ciudadanos", "0001_initial"),
    ]

    operations = [
        # 1. Agregar ciudadano_id en Inscripcion (nullable temporalmente)
        migrations.AddField(
            model_name="inscripcion",
            name="ciudadano",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="inscripciones_vat",
                to="ciudadanos.ciudadano",
                verbose_name="Ciudadano",
                null=True,
            ),
        ),
        # 2. Copiar persona__ciudadano_id → ciudadano_id (MySQL JOIN syntax)
        migrations.RunSQL(
            sql="""
                UPDATE VAT_inscripcion i
                INNER JOIN VAT_persona p ON i.persona_id = p.id
                SET i.ciudadano_id = p.ciudadano_id
                WHERE p.ciudadano_id IS NOT NULL;
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
        # 3. Eliminar índice persona+estado
        migrations.RunSQL(
            sql="DROP INDEX IF EXISTS vat_insc_per_est_idx ON VAT_inscripcion;",
            reverse_sql=migrations.RunSQL.noop,
        ),
        # 4. Eliminar FK persona de Inscripcion
        migrations.RemoveField(
            model_name="inscripcion",
            name="persona",
        ),
        # 5. Hacer ciudadano NOT NULL
        migrations.AlterField(
            model_name="inscripcion",
            name="ciudadano",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="inscripciones_vat",
                to="ciudadanos.ciudadano",
                verbose_name="Ciudadano",
            ),
        ),
        # 6. Actualizar unique_together
        migrations.AlterUniqueTogether(
            name="inscripcion",
            unique_together={("ciudadano", "comision")},
        ),
        # 7. Agregar índice ciudadano+estado
        migrations.AddIndex(
            model_name="inscripcion",
            index=models.Index(
                fields=["ciudadano", "estado"],
                name="vat_insc_ciu_est_idx",
            ),
        ),
        # 8. Eliminar modelo Persona
        migrations.DeleteModel(
            name="Persona",
        ),
    ]
