# Generated manually for AsignacionTecnico activa field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('celiaquia', '0008_cleanup_duplicated_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='asignaciontecnico',
            name='activa',
            field=models.BooleanField(default=True, help_text='Indica si la asignación está activa'),
        ),
        migrations.RemoveIndex(
            model_name='asignaciontecnico',
            name='asig_tecnico_idx',
        ),
        migrations.RemoveIndex(
            model_name='asignaciontecnico',
            name='asig_expediente_idx',
        ),
        migrations.AddIndex(
            model_name='asignaciontecnico',
            index=models.Index(fields=['tecnico', 'activa'], name='asig_tecnico_activa_idx'),
        ),
        migrations.AddIndex(
            model_name='asignaciontecnico',
            index=models.Index(fields=['expediente', 'activa'], name='asig_expediente_activa_idx'),
        ),
    ]