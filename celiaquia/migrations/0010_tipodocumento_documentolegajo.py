# Generated manually for TipoDocumento and DocumentoLegajo

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def crear_tipos_documento_iniciales(apps, schema_editor):
    """Crea los tipos de documento iniciales."""
    TipoDocumento = apps.get_model('celiaquia', 'TipoDocumento')
    
    tipos_iniciales = [
        {'nombre': 'DNI o Documento de Identidad', 'descripcion': 'Documento Nacional de Identidad del beneficiario', 'orden': 1},
        {'nombre': 'Certificado Médico Celíaco', 'descripcion': 'Certificado médico que acredita la condición celíaca', 'orden': 2},
        {'nombre': 'Comprobante de Ingresos', 'descripcion': 'Comprobante de ingresos familiares', 'orden': 3, 'requerido': False},
    ]
    
    for tipo_data in tipos_iniciales:
        TipoDocumento.objects.get_or_create(
            nombre=tipo_data['nombre'],
            defaults=tipo_data
        )


def migrar_archivos_existentes(apps, schema_editor):
    """Migra archivos existentes al nuevo sistema."""
    ExpedienteCiudadano = apps.get_model('celiaquia', 'ExpedienteCiudadano')
    TipoDocumento = apps.get_model('celiaquia', 'TipoDocumento')
    DocumentoLegajo = apps.get_model('celiaquia', 'DocumentoLegajo')
    
    # Obtener tipos de documento
    try:
        tipo_dni = TipoDocumento.objects.get(nombre='DNI o Documento de Identidad')
        tipo_certificado = TipoDocumento.objects.get(nombre='Certificado Médico Celíaco')
        tipo_ingresos = TipoDocumento.objects.get(nombre='Comprobante de Ingresos')
    except TipoDocumento.DoesNotExist:
        return  # Si no existen los tipos, no migrar
    
    legajos_con_archivos = ExpedienteCiudadano.objects.filter(
        models.Q(archivo1__isnull=False) |
        models.Q(archivo2__isnull=False) |
        models.Q(archivo3__isnull=False)
    ).exclude(
        models.Q(archivo1='') &
        models.Q(archivo2='') &
        models.Q(archivo3='')
    )
    
    for legajo in legajos_con_archivos:
        # Migrar archivo1 como DNI (si existe)
        if legajo.archivo1:
            DocumentoLegajo.objects.get_or_create(
                legajo=legajo,
                tipo_documento=tipo_dni,
                defaults={'archivo': legajo.archivo1}
            )
        
        # Migrar archivo2 como Certificado Médico (si existe)
        if legajo.archivo2:
            DocumentoLegajo.objects.get_or_create(
                legajo=legajo,
                tipo_documento=tipo_certificado,
                defaults={'archivo': legajo.archivo2}
            )
        
        # Migrar archivo3 como Comprobante de Ingresos (si existe)
        if legajo.archivo3:
            DocumentoLegajo.objects.get_or_create(
                legajo=legajo,
                tipo_documento=tipo_ingresos,
                defaults={'archivo': legajo.archivo3}
            )


def reversa_migracion(apps, schema_editor):
    """Reversa la migración."""
    TipoDocumento = apps.get_model('celiaquia', 'TipoDocumento')
    DocumentoLegajo = apps.get_model('celiaquia', 'DocumentoLegajo')
    
    DocumentoLegajo.objects.all().delete()
    TipoDocumento.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('celiaquia', '0009_asignaciontecnico_activa'),
    ]

    operations = [
        migrations.CreateModel(
            name='TipoDocumento',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=100, unique=True)),
                ('descripcion', models.TextField(blank=True)),
                ('requerido', models.BooleanField(default=True)),
                ('orden', models.PositiveIntegerField(default=0, help_text='Orden de presentación')),
                ('activo', models.BooleanField(default=True)),
            ],
            options={
                'verbose_name': 'Tipo de Documento',
                'verbose_name_plural': 'Tipos de Documento',
                'ordering': ['orden', 'nombre'],
            },
        ),
        migrations.CreateModel(
            name='DocumentoLegajo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('archivo', models.FileField(upload_to='legajos/documentos/')),
                ('fecha_carga', models.DateTimeField(auto_now_add=True)),
                ('observaciones', models.TextField(blank=True)),
                ('legajo', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='documentos',
                    to='celiaquia.expedienteciudadano'
                )),
                ('tipo_documento', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='documentos_legajo',
                    to='celiaquia.tipodocumento'
                )),
                ('usuario_carga', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='documentos_cargados',
                    to=settings.AUTH_USER_MODEL
                )),
            ],
            options={
                'verbose_name': 'Documento de Legajo',
                'verbose_name_plural': 'Documentos de Legajo',
                'ordering': ['-fecha_carga'],
            },
        ),
        migrations.AddIndex(
            model_name='documentolegajo',
            index=models.Index(fields=['legajo', 'tipo_documento'], name='celiaquia_d_legajo_b8b8c8_idx'),
        ),
        migrations.AddIndex(
            model_name='documentolegajo',
            index=models.Index(fields=['fecha_carga'], name='celiaquia_d_fecha_c_86d7a4_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='documentolegajo',
            unique_together={('legajo', 'tipo_documento')},
        ),
        migrations.RunPython(
            crear_tipos_documento_iniciales,
            reversa_migracion
        ),
        migrations.RunPython(
            migrar_archivos_existentes,
            migrations.RunPython.noop
        ),
    ]