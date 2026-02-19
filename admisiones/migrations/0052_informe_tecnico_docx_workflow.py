# Generated manually for DOCX workflow changes

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('admisiones', '0051_merge_20260120_1622'),
    ]

    operations = [
        migrations.AlterField(
            model_name='informetecnico',
            name='estado',
            field=models.CharField(
                choices=[
                    ('Iniciado', 'Iniciado'),
                    ('Para revision', 'Para revisión'),
                    ('Docx generado', 'DOCX generado'),
                    ('Docx editado', 'DOCX editado'),
                    ('Validado', 'Validado'),
                    ('A subsanar', 'A subsanar')
                ],
                max_length=20,
                verbose_name='Estado del Informe'
            ),
        ),
        migrations.AddField(
            model_name='informetecnico',
            name='observaciones_subsanacion',
            field=models.TextField(
                blank=True,
                help_text='Observaciones del abogado para subsanar el informe técnico',
                null=True,
                verbose_name='Observaciones de Subsanación'
            ),
        ),
        migrations.AlterField(
            model_name='admision',
            name='estado_admision',
            field=models.CharField(
                choices=[
                    ('iniciada', 'Iniciada'),
                    ('convenio_seleccionado', 'Convenio seleccionado'),
                    ('documentacion_en_proceso', 'Documentación en proceso'),
                    ('documentacion_finalizada', 'Documentación cargada'),
                    ('documentacion_aprobada', 'Documentación aprobada'),
                    ('expediente_cargado', 'Expediente cargado'),
                    ('informe_tecnico_en_proceso', 'Informe técnico en proceso'),
                    ('informe_tecnico_finalizado', 'Informe técnico finalizado'),
                    ('informe_tecnico_en_revision', 'Informe técnico en revisión'),
                    ('informe_tecnico_en_subsanacion', 'Informe técnico en subsanación'),
                    ('informe_tecnico_aprobado', 'Informe técnico aprobado'),
                    ('if_informe_tecnico_cargado', 'IF Informe técnico cargado'),
                    ('enviado_a_legales', 'Enviado a legales'),
                    ('enviado_a_acompaniamiento', 'Enviado a acompañamiento'),
                    ('inactivada', 'Inactivada'),
                    ('descartado', 'Descartado')
                ],
                default='iniciada',
                max_length=40,
                verbose_name='Estado de Admisión'
            ),
        ),
        migrations.AddField(
            model_name='informetecnicopdf',
            name='archivo_docx_editado',
            field=models.FileField(
                blank=True,
                help_text='DOCX editado por el técnico',
                null=True,
                upload_to='admisiones/informes_tecnicos/docx_editado'
            ),
        ),
    ]