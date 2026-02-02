# Generated manually

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def migrar_datos_a_nuevos_modelos(apps, schema_editor):
    """Migra datos de ExpedienteCiudadano a los nuevos modelos de auditoría"""
    ExpedienteCiudadano = apps.get_model("celiaquia", "ExpedienteCiudadano")
    ValidacionTecnica = apps.get_model("celiaquia", "ValidacionTecnica")
    CruceResultado = apps.get_model("celiaquia", "CruceResultado")
    CupoTitular = apps.get_model("celiaquia", "CupoTitular")
    ValidacionRenaper = apps.get_model("celiaquia", "ValidacionRenaper")
    
    db_alias = schema_editor.connection.alias
    
    for legajo in ExpedienteCiudadano.objects.using(db_alias).all():
        ValidacionTecnica.objects.using(db_alias).create(
            legajo=legajo,
            revision_tecnico=legajo.revision_tecnico,
            subsanacion_motivo=legajo.subsanacion_motivo,
            subsanacion_solicitada_en=legajo.subsanacion_solicitada_en,
            subsanacion_enviada_en=legajo.subsanacion_enviada_en,
            subsanacion_usuario=legajo.subsanacion_usuario,
        )
        
        CruceResultado.objects.using(db_alias).create(
            legajo=legajo,
            resultado_sintys=legajo.resultado_sintys,
            cruce_ok=legajo.cruce_ok,
            observacion_cruce=legajo.observacion_cruce,
        )
        
        CupoTitular.objects.using(db_alias).create(
            legajo=legajo,
            estado_cupo=legajo.estado_cupo,
            es_titular_activo=legajo.es_titular_activo,
        )
        
        ValidacionRenaper.objects.using(db_alias).create(
            legajo=legajo,
            estado_validacion=legajo.estado_validacion_renaper,
            comentario=legajo.subsanacion_renaper_comentario,
            archivo=legajo.subsanacion_renaper_archivo,
        )


def reverse_migration(apps, schema_editor):
    """Rollback: elimina los registros de los nuevos modelos"""
    ValidacionTecnica = apps.get_model("celiaquia", "ValidacionTecnica")
    CruceResultado = apps.get_model("celiaquia", "CruceResultado")
    CupoTitular = apps.get_model("celiaquia", "CupoTitular")
    ValidacionRenaper = apps.get_model("celiaquia", "ValidacionRenaper")
    
    db_alias = schema_editor.connection.alias
    
    ValidacionTecnica.objects.using(db_alias).all().delete()
    CruceResultado.objects.using(db_alias).all().delete()
    CupoTitular.objects.using(db_alias).all().delete()
    ValidacionRenaper.objects.using(db_alias).all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('celiaquia', '0004_registroerroneo'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('ciudadanos', '0004_alter_ciudadano_telefono_and_more'),
    ]

    operations = [
        # 1. Agregar campo rol a ExpedienteCiudadano
        migrations.AddField(
            model_name='expedienteciudadano',
            name='rol',
            field=models.CharField(
                choices=[
                    ('beneficiario', 'Solo Beneficiario'),
                    ('responsable', 'Solo Responsable'),
                    ('beneficiario_y_responsable', 'Beneficiario y Responsable')
                ],
                default='beneficiario',
                max_length=50,
                db_index=True
            ),
        ),
        
        # 2. Agregar índice en ExpedienteEstadoHistorial
        migrations.AddIndex(
            model_name='expedienteestadohistorial',
            index=models.Index(fields=['expediente', '-fecha'], name='exp_hist_exp_fecha_idx'),
        ),
        
        # 3. Agregar índice compuesto en ExpedienteCiudadano
        migrations.AddIndex(
            model_name='expedienteciudadano',
            index=models.Index(fields=['estado_cupo', 'es_titular_activo', 'rol'], name='leg_cupo_activo_rol_idx'),
        ),
        
        # 4-11. Crear los 8 nuevos modelos (ValidacionTecnica, CruceResultado, etc.)
        migrations.CreateModel(
            name='ValidacionTecnica',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('revision_tecnico', models.CharField(choices=[('PENDIENTE', 'Pendiente'), ('APROBADO', 'Aprobado por el tecnico'), ('RECHAZADO', 'Rechazado por el tecnico'), ('SUBSANAR', 'Subsanar'), ('SUBSANADO', 'Subsanado')], default='PENDIENTE', max_length=24)),
                ('subsanacion_motivo', models.TextField(blank=True, null=True)),
                ('subsanacion_solicitada_en', models.DateTimeField(blank=True, null=True)),
                ('subsanacion_enviada_en', models.DateTimeField(blank=True, null=True)),
                ('creado_en', models.DateTimeField(auto_now_add=True)),
                ('modificado_en', models.DateTimeField(auto_now=True)),
                ('legajo', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='validacion_tecnica', to='celiaquia.expedienteciudadano')),
                ('subsanacion_usuario', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='validaciones_tecnicas', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Validación Técnica',
                'verbose_name_plural': 'Validaciones Técnicas',
            },
        ),
        migrations.CreateModel(
            name='CruceResultado',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('resultado_sintys', models.CharField(choices=[('SIN_CRUCE', 'Sin cruce'), ('MATCH', 'Matcheado'), ('NO_MATCH', 'No matcheado')], default='SIN_CRUCE', max_length=10)),
                ('cruce_ok', models.BooleanField(blank=True, null=True)),
                ('observacion_cruce', models.CharField(blank=True, max_length=255, null=True)),
                ('creado_en', models.DateTimeField(auto_now_add=True)),
                ('modificado_en', models.DateTimeField(auto_now=True)),
                ('legajo', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='cruce_resultado', to='celiaquia.expedienteciudadano')),
            ],
            options={
                'verbose_name': 'Resultado de Cruce',
                'verbose_name_plural': 'Resultados de Cruce',
            },
        ),
        migrations.CreateModel(
            name='CupoTitular',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('estado_cupo', models.CharField(choices=[('NO_EVAL', 'No evaluado'), ('DENTRO', 'Dentro de cupo'), ('FUERA', 'Fuera de cupo')], default='NO_EVAL', max_length=8)),
                ('es_titular_activo', models.BooleanField(default=False)),
                ('creado_en', models.DateTimeField(auto_now_add=True)),
                ('modificado_en', models.DateTimeField(auto_now=True)),
                ('legajo', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='cupo_titular', to='celiaquia.expedienteciudadano')),
            ],
            options={
                'verbose_name': 'Cupo Titular',
                'verbose_name_plural': 'Cupos Titulares',
            },
        ),
        migrations.AddIndex(
            model_name='cupotitular',
            index=models.Index(fields=['estado_cupo', 'es_titular_activo'], name='celiaquia_c_estado__idx'),
        ),
        migrations.CreateModel(
            name='ValidacionRenaper',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('estado_validacion', models.IntegerField(choices=[(0, 'No validado'), (1, 'Aceptado'), (2, 'Rechazado'), (3, 'Subsanar')], default=0)),
                ('comentario', models.TextField(blank=True, null=True)),
                ('archivo', models.FileField(blank=True, null=True, upload_to='legajos/subsanacion_renaper/')),
                ('creado_en', models.DateTimeField(auto_now_add=True)),
                ('modificado_en', models.DateTimeField(auto_now=True)),
                ('legajo', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='validacion_renaper', to='celiaquia.expedienteciudadano')),
            ],
            options={
                'verbose_name': 'Validación Renaper',
                'verbose_name_plural': 'Validaciones Renaper',
            },
        ),
        migrations.CreateModel(
            name='HistorialValidacionTecnica',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('estado_anterior', models.CharField(blank=True, choices=[('PENDIENTE', 'Pendiente'), ('APROBADO', 'Aprobado por el tecnico'), ('RECHAZADO', 'Rechazado por el tecnico'), ('SUBSANAR', 'Subsanar'), ('SUBSANADO', 'Subsanado')], max_length=24, null=True)),
                ('estado_nuevo', models.CharField(choices=[('PENDIENTE', 'Pendiente'), ('APROBADO', 'Aprobado por el tecnico'), ('RECHAZADO', 'Rechazado por el tecnico'), ('SUBSANAR', 'Subsanar'), ('SUBSANADO', 'Subsanado')], max_length=24)),
                ('motivo', models.TextField(blank=True, null=True)),
                ('creado_en', models.DateTimeField(auto_now_add=True)),
                ('legajo', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='historial_validacion_tecnica', to='celiaquia.expedienteciudadano')),
                ('usuario', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='cambios_validacion_tecnica', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Historial Validación Técnica',
                'verbose_name_plural': 'Historiales Validación Técnica',
                'ordering': ('-creado_en',),
            },
        ),
        migrations.AddIndex(
            model_name='historialvalidaciontecnica',
            index=models.Index(fields=['legajo', '-creado_en'], name='celiaquia_h_legajo__idx'),
        ),
        migrations.CreateModel(
            name='HistorialCupo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('estado_cupo_anterior', models.CharField(blank=True, choices=[('NO_EVAL', 'No evaluado'), ('DENTRO', 'Dentro de cupo'), ('FUERA', 'Fuera de cupo')], max_length=8, null=True)),
                ('estado_cupo_nuevo', models.CharField(choices=[('NO_EVAL', 'No evaluado'), ('DENTRO', 'Dentro de cupo'), ('FUERA', 'Fuera de cupo')], max_length=8)),
                ('es_titular_activo_anterior', models.BooleanField(blank=True, null=True)),
                ('es_titular_activo_nuevo', models.BooleanField()),
                ('tipo_movimiento', models.CharField(choices=[('ALTA', 'Alta'), ('REACTIVACION', 'Reactivacion'), ('BAJA', 'Baja'), ('AJUSTE', 'Ajuste'), ('SUSPENDIDO', 'Suspendido')], max_length=20)),
                ('motivo', models.TextField(blank=True, null=True)),
                ('creado_en', models.DateTimeField(auto_now_add=True)),
                ('legajo', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='historial_cupo', to='celiaquia.expedienteciudadano')),
                ('usuario', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='cambios_cupo', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Historial Cupo',
                'verbose_name_plural': 'Historiales Cupo',
                'ordering': ('-creado_en',),
            },
        ),
        migrations.AddIndex(
            model_name='historialcupo',
            index=models.Index(fields=['legajo', '-creado_en'], name='celiaquia_h_legajo__idx2'),
        ),
        migrations.AddIndex(
            model_name='historialcupo',
            index=models.Index(fields=['tipo_movimiento', '-creado_en'], name='celiaquia_h_tipo_mo__idx'),
        ),
        migrations.CreateModel(
            name='SubsanacionRespuesta',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('archivo1', models.FileField(blank=True, null=True, upload_to='legajos/subsanacion_respuesta/')),
                ('archivo2', models.FileField(blank=True, null=True, upload_to='legajos/subsanacion_respuesta/')),
                ('archivo3', models.FileField(blank=True, null=True, upload_to='legajos/subsanacion_respuesta/')),
                ('comentario', models.TextField(blank=True, null=True)),
                ('creado_en', models.DateTimeField(auto_now_add=True)),
                ('legajo', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='subsanaciones_respuestas', to='celiaquia.expedienteciudadano')),
                ('validacion_tecnica', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='respuestas', to='celiaquia.validaciontecnica')),
                ('usuario', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='subsanaciones_respondidas', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Respuesta de Subsanación',
                'verbose_name_plural': 'Respuestas de Subsanación',
                'ordering': ('-creado_en',),
            },
        ),
        migrations.AddIndex(
            model_name='subsanacionrespuesta',
            index=models.Index(fields=['legajo', '-creado_en'], name='celiaquia_s_legajo__idx'),
        ),
        migrations.AddIndex(
            model_name='subsanacionrespuesta',
            index=models.Index(fields=['validacion_tecnica'], name='celiaquia_s_validac__idx'),
        ),
        migrations.CreateModel(
            name='RegistroErroneoReprocesado',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('intento_numero', models.PositiveIntegerField()),
                ('resultado', models.CharField(choices=[('EXITOSO', 'Exitoso'), ('FALLIDO', 'Fallido')], max_length=10)),
                ('error_mensaje', models.TextField(blank=True, null=True)),
                ('creado_en', models.DateTimeField(auto_now_add=True)),
                ('ciudadano_creado', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='ciudadanos.ciudadano')),
                ('legajo_creado', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='celiaquia.expedienteciudadano')),
                ('registro_erroneo', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reprocesados', to='celiaquia.registroerroneo')),
                ('usuario', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='reprocesados', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Registro Erróneo Reprocesado',
                'verbose_name_plural': 'Registros Erróneos Reprocesados',
                'ordering': ('-creado_en',),
            },
        ),
        migrations.AddConstraint(
            model_name='registroerroneoreprocesado',
            constraint=models.UniqueConstraint(fields=('registro_erroneo', 'intento_numero'), name='celiaquia_registroerroneoreprocesado_unique'),
        ),
        migrations.AddIndex(
            model_name='registroerroneoreprocesado',
            index=models.Index(fields=['registro_erroneo', '-creado_en'], name='celiaquia_r_registr__idx'),
        ),
        migrations.AddIndex(
            model_name='registroerroneoreprocesado',
            index=models.Index(fields=['resultado'], name='celiaquia_r_resulta__idx'),
        ),
        
        # 12. Migrar datos existentes
        migrations.RunPython(migrar_datos_a_nuevos_modelos, reverse_migration),
    ]
