# Generated migration - 100% SAFE (no automatic data migration)
# This migration ONLY adds fields and models, does NOT migrate data

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('celiaquia', '0005_add_rol_and_new_models'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # 1. Crear nuevos modelos (sin datos)
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
            options={'verbose_name': 'Validacion Tecnica', 'verbose_name_plural': 'Validaciones Tecnicas'},
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
            options={'verbose_name': 'Resultado de Cruce', 'verbose_name_plural': 'Resultados de Cruce'},
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
            options={'verbose_name': 'Cupo Titular', 'verbose_name_plural': 'Cupos Titulares'},
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
            options={'verbose_name': 'Validacion Renaper', 'verbose_name_plural': 'Validaciones Renaper'},
        ),
    ]
