# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('admisiones', '0033_remove_archivoadmision_orden_documentacion_orden'),
    ]

    operations = [
        migrations.AddField(
            model_name='admision',
            name='estado_admision',
            field=models.CharField(
                choices=[
                    ('iniciada', 'Iniciada'),
                    ('convenio_seleccionado', 'Convenio seleccionado'),
                    ('documentacion_en_proceso', 'Documentación en proceso'),
                    ('documentacion_finalizada', 'Documentación finalizada'),
                    ('documentacion_aprobada', 'Documentación aprobada'),
                    ('expediente_cargado', 'Expediente cargado'),
                    ('informe_tecnico_en_proceso', 'Informe técnico en proceso'),
                    ('informe_tecnico_en_revision', 'Informe técnico en revisión'),
                    ('informe_tecnico_en_subsanacion', 'Informe técnico en subsanación'),
                    ('informe_tecnico_aprobado', 'Informe técnico aprobado'),
                    ('enviado_a_legales', 'Enviado a legales'),
                ],
                default='iniciada',
                max_length=40,
                verbose_name='Estado de Admisión'
            ),
        ),
    ]