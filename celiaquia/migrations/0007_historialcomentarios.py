# Generated manually for HistorialComentarios

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def migrar_comentarios_existentes(apps, schema_editor):
    """Migra comentarios existentes al historial."""
    ExpedienteCiudadano = apps.get_model('celiaquia', 'ExpedienteCiudadano')
    HistorialComentarios = apps.get_model('celiaquia', 'HistorialComentarios')
    
    from django.db import models as django_models
    
    legajos_con_comentarios = ExpedienteCiudadano.objects.filter(
        django_models.Q(subsanacion_motivo__isnull=False) |
        django_models.Q(subsanacion_renaper_comentario__isnull=False) |
        django_models.Q(observacion_cruce__isnull=False)
    ).exclude(
        django_models.Q(subsanacion_motivo='') &
        django_models.Q(subsanacion_renaper_comentario='') &
        django_models.Q(observacion_cruce='')
    )
    
    for legajo in legajos_con_comentarios:
        # Migrar motivo de subsanación
        if legajo.subsanacion_motivo:
            HistorialComentarios.objects.create(
                legajo=legajo,
                tipo_comentario='SUBSANACION_MOTIVO',
                comentario=legajo.subsanacion_motivo,
                usuario=legajo.subsanacion_usuario,
                estado_relacionado='SUBSANAR'
            )
        
        # Migrar comentario RENAPER
        if legajo.subsanacion_renaper_comentario:
            HistorialComentarios.objects.create(
                legajo=legajo,
                tipo_comentario='RENAPER_VALIDACION',
                comentario=legajo.subsanacion_renaper_comentario,
                estado_relacionado=str(legajo.estado_validacion_renaper)
            )
        
        # Migrar observación de cruce
        if legajo.observacion_cruce:
            HistorialComentarios.objects.create(
                legajo=legajo,
                tipo_comentario='CRUCE_SINTYS',
                comentario=legajo.observacion_cruce,
                estado_relacionado=legajo.resultado_sintys
            )


def reversa_migracion(apps, schema_editor):
    """Reversa la migración eliminando comentarios migrados."""
    HistorialComentarios = apps.get_model('celiaquia', 'HistorialComentarios')
    HistorialComentarios.objects.filter(
        tipo_comentario__in=['SUBSANACION_MOTIVO', 'RENAPER_VALIDACION', 'CRUCE_SINTYS']
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('celiaquia', '0006_remove_registroerroneoreprocesado_celiaquia_registroerroneoreprocesado_unique_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='HistorialComentarios',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tipo_comentario', models.CharField(
                    choices=[
                        ('VALIDACION_TECNICA', 'Validación Técnica'),
                        ('SUBSANACION_MOTIVO', 'Motivo de Subsanación'),
                        ('SUBSANACION_RESPUESTA', 'Respuesta de Subsanación'),
                        ('RENAPER_VALIDACION', 'Validación RENAPER'),
                        ('OBSERVACION_GENERAL', 'Observación General'),
                        ('CRUCE_SINTYS', 'Cruce SINTYS'),
                        ('PAGO_OBSERVACION', 'Observación de Pago'),
                    ],
                    db_index=True,
                    max_length=30
                )),
                ('comentario', models.TextField()),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True)),
                ('archivo_adjunto', models.FileField(blank=True, null=True, upload_to='comentarios/')),
                ('estado_relacionado', models.CharField(
                    blank=True,
                    help_text='Estado del legajo al momento del comentario',
                    max_length=50,
                    null=True
                )),
                ('legajo', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='historial_comentarios',
                    to='celiaquia.expedienteciudadano'
                )),
                ('usuario', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='comentarios_realizados',
                    to=settings.AUTH_USER_MODEL
                )),
            ],
            options={
                'verbose_name': 'Historial de Comentarios',
                'verbose_name_plural': 'Historial de Comentarios',
                'ordering': ('-fecha_creacion',),
            },
        ),
        migrations.AddIndex(
            model_name='historialcomentarios',
            index=models.Index(fields=['legajo', '-fecha_creacion'], name='celiaquia_h_legajo_b8b8c8_idx'),
        ),
        migrations.AddIndex(
            model_name='historialcomentarios',
            index=models.Index(fields=['tipo_comentario', '-fecha_creacion'], name='celiaquia_h_tipo_co_86d7a4_idx'),
        ),
        migrations.AddIndex(
            model_name='historialcomentarios',
            index=models.Index(fields=['usuario', '-fecha_creacion'], name='celiaquia_h_usuario_f2e1a3_idx'),
        ),
        migrations.RunPython(
            migrar_comentarios_existentes,
            reversa_migracion
        ),
    ]