import logging

import core.fields
import core.soft_delete.base
from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone

logger = logging.getLogger("django")


def limpiar_cache_territorial(apps, schema_editor):
    TerritorialCache = apps.get_model("comedores", "TerritorialCache")
    deleted_count = TerritorialCache.objects.all().count()
    TerritorialCache.objects.all().delete()
    logger.info("Eliminados %s registros de cache territorial existentes", deleted_count)
    logger.info("El cache será regenerado automáticamente por provincia en el primer uso")


def reverse_limpiar_cache(apps, schema_editor):
    pass


STATE_TRANSITIONS = {
    "Activo": {"actividad": "Activo", "proceso": "En ejecución"},
    "Inactivo": {"actividad": "Inactivo", "proceso": "Baja"},
    "En proceso - Incorporación": {"actividad": "Inactivo", "proceso": "En proceso - Incorporación"},
    "En proceso - Renovación": {"actividad": "Activo", "proceso": "En proceso - Renovación"},
    "Sin definir": {"actividad": "Inactivo", "proceso": None},
}


def crear_historial_inicial(apps, schema_editor):
    Comedor = apps.get_model("comedores", "Comedor")
    EstadoActividad = apps.get_model("comedores", "EstadoActividad")
    EstadoProceso = apps.get_model("comedores", "EstadoProceso")
    EstadoDetalle = apps.get_model("comedores", "EstadoDetalle")
    EstadoGeneral = apps.get_model("comedores", "EstadoGeneral")
    EstadoHistorial = apps.get_model("comedores", "EstadoHistorial")
    actividades = {}
    procesos = {}
    for config in STATE_TRANSITIONS.values():
        act_name = config["actividad"]
        actividad, _ = EstadoActividad.objects.get_or_create(estado=act_name)
        actividades[act_name] = actividad
        proc_name = config.get("proceso")
        if proc_name:
            procesos[(act_name, proc_name)], _ = EstadoProceso.objects.get_or_create(
                estado=proc_name,
                estado_actividad=actividad,
            )
    for comedor in Comedor.objects.all():
        estado_prev = (getattr(comedor, "estado_general", None) or "").strip()
        config = STATE_TRANSITIONS.get(estado_prev)
        if not config:
            continue
        actividad = actividades.get(config["actividad"])
        proc_name = config.get("proceso")
        proceso = procesos.get((config["actividad"], proc_name)) if proc_name else None
        if not actividad or (proc_name and not proceso):
            continue
        detalle_label = config.get("detalle")
        detalle = None
        if detalle_label:
            detalle, _ = EstadoDetalle.objects.get_or_create(
                estado=detalle_label,
                estado_proceso=proceso,
            )
        estado_general_obj, _ = EstadoGeneral.objects.get_or_create(
            estado_actividad=actividad,
            estado_proceso=proceso,
            estado_detalle=detalle,
        )
        historial = EstadoHistorial.objects.create(
            comedor=comedor,
            estado_general=estado_general_obj,
        )
        comedor.ultimo_estado = historial
        comedor.save(update_fields=["ultimo_estado"])


def _map_legacy_nombre(nombre):
    if not nombre:
        return "pendiente"
    normalized = nombre.strip().lower()
    if normalized in {"pendiente", "pendientes"} or "pend" in normalized:
        return "pendiente"
    if normalized in {"activo", "activos"} or "act" in normalized or "habil" in normalized:
        return "activo"
    if (
        normalized in {"baja", "bajas", "inactivo", "inactivos"}
        or "baj" in normalized
        or "inac" in normalized
        or "fin" in normalized
        or "cerr" in normalized
    ):
        return "baja"
    return "pendiente"


def copy_estado_forward(apps, schema_editor):
    Nomina = apps.get_model("comedores", "Nomina")
    try:
        EstadoIntervencion = apps.get_model("ciudadanos", "EstadoIntervencion")
    except LookupError:
        EstadoIntervencion = None
    db_alias = schema_editor.connection.alias
    legacy_map = {}
    if EstadoIntervencion is not None:
        legacy_map = {
            estado.pk: _map_legacy_nombre(getattr(estado, "nombre", ""))
            for estado in EstadoIntervencion.objects.using(db_alias).all()
        }
    for nomina in Nomina.objects.using(db_alias).all():
        legacy_value = legacy_map.get(getattr(nomina, "estado_id", None))
        if legacy_value is None:
            legacy_value = getattr(nomina, "estado", None)
            if legacy_value not in {"pendiente", "activo", "baja"}:
                legacy_value = _map_legacy_nombre(str(legacy_value or ""))
        Nomina.objects.using(db_alias).filter(pk=nomina.pk).update(
            estado_nuevo=legacy_value or "pendiente"
        )


def copy_estado_backward(apps, schema_editor):
    Nomina = apps.get_model("comedores", "Nomina")
    Nomina.objects.using(schema_editor.connection.alias).update(estado=None)


class Migration(migrations.Migration):

    replaces = [
        ("comedores", "0001_initial"),
        ("comedores", "0002_remove_nomina_apellido_remove_nomina_dni_and_more"),
        ("comedores", "0003_alter_comedor_localidad_alter_comedor_municipio_and_more"),
        ("comedores", "0004_alter_observacion_unique_together"),
        ("comedores", "0005_territorialcache_territorialsynclog"),
        ("comedores", "0006_add_provincia_to_territorial_cache"),
        ("comedores", "0007_rename_comedores_territorial_provincia_activo_idx_comedores_t_provinc_38a553_idx"),
        ("comedores", "0008_comedor_estado_general"),
        ("comedores", "0009_alter_comedor_estado_general"),
        ("comedores", "0010_comedor_fecha_creacion"),
        ("comedores", "0011_auditcomedorprograma"),
        ("comedores", "0012_alter_comedor_estado_general"),
        ("comedores", "0014_comedor_estado_validacion_comedor_fecha_validado_and_more"),
        ("comedores", "0015_rename_comedores_h_comedor_b8b8c8_idx_comedores_h_comedor_86d7a4_idx"),
        ("comedores", "0013_estadoactividad_estadodetalle_estadogeneral_and_more"),
        ("comedores", "0016_merge_20251115_1706"),
        ("comedores", "0017_alter_comedor_estado_validacion"),
        ("comedores", "0018_add_opciones_no_validar"),
        ("comedores", "0013_alter_nomina_estado"),
        ("comedores", "0019_merge_20251125_1049"),
        ("comedores", "0020_alter_comedor_comienzo"),
        ("comedores", "0021_alter_nomina_estado"),
        ("comedores", "0022_alter_referente_mail_unicode"),
        ("comedores", "0023_alter_comedor_managers_alter_nomina_managers_and_more"),
    ]

    initial = True

    dependencies = [
        ("core", "0001_squashed_0007"),
        ("organizaciones", "0001_squashed_0010"),
        ("duplas", "0001_squashed_0003"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("ciudadanos", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name='CategoriaComedor',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=255)),
                ('puntuacion_min', models.IntegerField()),
                ('puntuacion_max', models.IntegerField()),
            ],
            options={
                'verbose_name': 'Categoria de Comedor',
                'verbose_name_plural': 'Categorias de Comedor',
            },
        ),
        migrations.CreateModel(
            name='Comedor',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=255)),
                ('id_externo', models.IntegerField(blank=True, null=True, verbose_name='Id Externo')),
                ('codigo_de_proyecto', models.CharField(blank=True, max_length=255, null=True, verbose_name='Código de Proyecto')),
                ('comienzo', models.IntegerField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(1900), django.core.validators.MaxValueValidator(2025)], verbose_name='Año en el que comenzó a funcionar')),
                ('estado', models.CharField(blank=True, choices=[('Sin Ingreso', 'Sin Ingreso'), ('Asignado a Dupla Técnica', 'Asignado a Dupla Técnica')], default='Sin Ingreso', max_length=255, null=True)),
                ('calle', models.CharField(blank=True, max_length=255, null=True, validators=[django.core.validators.RegexValidator(message='La dirección solo puede contener letras, números, espacios y los caracteres ., -', regex='^[a-zA-Z0-9\\s.,áéíóúÁÉÍÓÚñÑ-]*$')])),
                ('numero', models.PositiveIntegerField(blank=True, null=True)),
                ('piso', models.CharField(blank=True, max_length=255, null=True, validators=[django.core.validators.RegexValidator(message='La dirección solo puede contener letras, números, espacios y los caracteres ., -', regex='^[a-zA-Z0-9\\s.,áéíóúÁÉÍÓÚñÑ-]*$')])),
                ('departamento', models.CharField(blank=True, max_length=255, null=True, validators=[django.core.validators.RegexValidator(message='La dirección solo puede contener letras, números, espacios y los caracteres ., -', regex='^[a-zA-Z0-9\\s.,áéíóúÁÉÍÓÚñÑ-]*$')])),
                ('manzana', models.CharField(blank=True, max_length=255, null=True, validators=[django.core.validators.RegexValidator(message='La dirección solo puede contener letras, números, espacios y los caracteres ., -', regex='^[a-zA-Z0-9\\s.,áéíóúÁÉÍÓÚñÑ-]*$')])),
                ('lote', models.CharField(blank=True, max_length=255, null=True, validators=[django.core.validators.RegexValidator(message='La dirección solo puede contener letras, números, espacios y los caracteres ., -', regex='^[a-zA-Z0-9\\s.,áéíóúÁÉÍÓÚñÑ-]*$')])),
                ('entre_calle_1', models.CharField(blank=True, max_length=255, null=True, validators=[django.core.validators.RegexValidator(message='La dirección solo puede contener letras, números, espacios y los caracteres ., -', regex='^[a-zA-Z0-9\\s.,áéíóúÁÉÍÓÚñÑ-]*$')])),
                ('entre_calle_2', models.CharField(blank=True, max_length=255, null=True, validators=[django.core.validators.RegexValidator(message='La dirección solo puede contener letras, números, espacios y los caracteres ., -', regex='^[a-zA-Z0-9\\s.,áéíóúÁÉÍÓÚñÑ-]*$')])),
                ('latitud', models.FloatField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(-90), django.core.validators.MaxValueValidator(90)])),
                ('longitud', models.FloatField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(-180), django.core.validators.MaxValueValidator(180)])),
                ('partido', models.CharField(blank=True, max_length=255, null=True)),
                ('barrio', models.CharField(blank=True, max_length=255, null=True)),
                ('codigo_postal', models.IntegerField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(1000), django.core.validators.MaxValueValidator(999999)])),
                ('foto_legajo', models.ImageField(blank=True, null=True, upload_to='comedor/')),
                ('dupla', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='duplas.dupla')),
                ('localidad', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='core.localidad')),
                ('municipio', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='core.municipio')),
                ('organizacion', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='organizaciones.organizacion')),
            ],
            options={
                'verbose_name': 'comedor',
                'verbose_name_plural': 'comedores',
                'ordering': ['nombre'],
            },
        ),
        migrations.CreateModel(
            name='Programas',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=255)),
            ],
            options={
                'verbose_name': 'Programa',
                'verbose_name_plural': 'Programas',
                'ordering': ['id'],
            },
        ),
        migrations.CreateModel(
            name='Referente',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(blank=True, max_length=255, null=True, verbose_name='Nombre del referente')),
                ('apellido', models.CharField(blank=True, max_length=255, null=True, verbose_name='Apellido del referente')),
                ('mail', models.EmailField(blank=True, max_length=254, null=True, verbose_name='Mail del referente')),
                ('celular', models.BigIntegerField(blank=True, null=True, verbose_name='Celular del referente')),
                ('documento', models.BigIntegerField(blank=True, null=True, verbose_name='Documento del referente')),
                ('funcion', models.CharField(blank=True, max_length=255, null=True, verbose_name='Funcion del referente')),
            ],
            options={
                'verbose_name': 'Referente',
                'verbose_name_plural': 'Referentes',
            },
        ),
        migrations.CreateModel(
            name='TipoDeComedor',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=255)),
            ],
            options={
                'verbose_name': 'Tipo de comedor',
                'verbose_name_plural': 'Tipos de comedor',
                'ordering': ['id'],
            },
        ),
        migrations.CreateModel(
            name='ValorComida',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tipo', models.CharField(max_length=50)),
                ('valor', models.DecimalField(decimal_places=2, max_digits=10)),
                ('fecha', models.DateField()),
            ],
        ),
        migrations.CreateModel(
            name='ImagenComedor',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('imagen', models.ImageField(upload_to='comedor/')),
                ('comedor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='imagenes', to='comedores.comedor')),
            ],
        ),
        migrations.AddField(
            model_name='comedor',
            name='programa',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='comedores.programas'),
        ),
        migrations.AddField(
            model_name='comedor',
            name='provincia',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to='core.provincia'),
        ),
        migrations.AddField(
            model_name='comedor',
            name='referente',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='comedores.referente'),
        ),
        migrations.AddField(
            model_name='comedor',
            name='tipocomedor',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='comedores.tipodecomedor'),
        ),
        migrations.CreateModel(
            name='Observacion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('observador', models.CharField(blank=True, max_length=255)),
                ('fecha_visita', models.DateTimeField(blank=True, default=django.utils.timezone.now)),
                ('observacion', models.TextField()),
                ('comedor', models.ForeignKey(blank=True, on_delete=django.db.models.deletion.CASCADE, to='comedores.comedor')),
            ],
            options={
                'verbose_name': 'Observacion',
                'verbose_name_plural': 'Observaciones',
                'indexes': [models.Index(fields=['comedor'], name='comedores_o_comedor_36d2df_idx')],
                'unique_together': {('comedor', 'fecha_visita')},
            },
        ),
        migrations.CreateModel(
            name='Nomina',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fecha', models.DateTimeField(auto_now_add=True)),
                ('observaciones', models.TextField(blank=True, null=True)),
                ('nombre', models.TextField(blank=True, null=True)),
                ('apellido', models.TextField(blank=True, null=True)),
                ('dni', models.IntegerField(blank=True, null=True)),
                ('comedor', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='comedores.comedor')),
                ('estado', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='ciudadanos.estadointervencion')),
                ('sexo', models.ForeignKey(default=1, null=True, on_delete=django.db.models.deletion.SET_NULL, to='core.sexo')),
            ],
            options={
                'verbose_name': 'Nomina',
                'verbose_name_plural': 'Nominas',
                'ordering': ['-fecha'],
                'indexes': [models.Index(fields=['comedor'], name='comedores_n_comedor_2179d8_idx')],
            },
        ),
        migrations.AddIndex(
            model_name='comedor',
            index=models.Index(fields=['nombre'], name='comedores_c_nombre_a1fc3f_idx'),
        ),
        migrations.RemoveField(
            model_name='nomina',
            name='apellido',
        ),
        migrations.RemoveField(
            model_name='nomina',
            name='dni',
        ),
        migrations.RemoveField(
            model_name='nomina',
            name='nombre',
        ),
        migrations.RemoveField(
            model_name='nomina',
            name='sexo',
        ),
        migrations.AddField(
            model_name='nomina',
            name='ciudadano',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='nominas', to='ciudadanos.ciudadano'),
        ),
        migrations.AlterField(
            model_name='comedor',
            name='localidad',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='core.localidad'),
        ),
        migrations.AlterField(
            model_name='comedor',
            name='municipio',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='core.municipio'),
        ),
        migrations.AlterField(
            model_name='comedor',
            name='provincia',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to='core.provincia'),
        ),
        migrations.AlterUniqueTogether(
            name='observacion',
            unique_together=set(),
        ),
        migrations.CreateModel(
            name='TerritorialCache',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('gestionar_uid', models.CharField(max_length=100, unique=True)),
                ('nombre', models.CharField(max_length=200)),
                ('activo', models.BooleanField(default=True)),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True)),
                ('fecha_actualizacion', models.DateTimeField(auto_now=True)),
                ('fecha_ultimo_sync', models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={
                'verbose_name': 'Cache Territorial',
                'verbose_name_plural': 'Cache Territoriales',
                'db_table': 'comedores_territorial_cache',
                'ordering': ['nombre'],
            },
        ),
        migrations.CreateModel(
            name='TerritorialSyncLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fecha', models.DateTimeField(auto_now_add=True)),
                ('exitoso', models.BooleanField()),
                ('territoriales_sincronizados', models.IntegerField(default=0)),
                ('error_mensaje', models.TextField(blank=True)),
                ('comedor_id', models.IntegerField(blank=True, null=True)),
            ],
            options={
                'verbose_name': 'Log Sync Territorial',
                'verbose_name_plural': 'Logs Sync Territoriales',
                'db_table': 'comedores_territorial_sync_log',
                'ordering': ['-fecha'],
            },
        ),
        migrations.RunPython(
            code=limpiar_cache_territorial,
            reverse_code=reverse_limpiar_cache,
        ),
        migrations.AddField(
            model_name='territorialcache',
            name='provincia',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.provincia'),
        ),
        migrations.AlterField(
            model_name='territorialcache',
            name='gestionar_uid',
            field=models.CharField(max_length=100),
        ),
        migrations.AlterUniqueTogether(
            name='territorialcache',
            unique_together={('gestionar_uid', 'provincia')},
        ),
        migrations.AddIndex(
            model_name='territorialcache',
            index=models.Index(fields=['provincia', 'activo'], name='comedores_territorial_provincia_activo_idx'),
        ),
        migrations.AlterModelOptions(
            name='territorialcache',
            options={'ordering': ['provincia__nombre', 'nombre'], 'verbose_name': 'Cache Territorial', 'verbose_name_plural': 'Cache Territoriales'},
        ),
        migrations.RenameIndex(
            model_name='territorialcache',
            new_name='comedores_t_provinc_38a553_idx',
            old_name='comedores_territorial_provincia_activo_idx',
        ),
        migrations.AddField(
            model_name='comedor',
            name='estado_general',
            field=models.CharField(choices=[('Activo', 'Activo'), ('Inactivo', 'Inactivo'), ('En proceso - Incorporación', 'En proceso - Incorporación'), ('En proceso - Renovación', 'En proceso - Renovación'), ('Sin definir', 'Sin definir')], default='Sin definir', max_length=32, verbose_name='Estado general'),
        ),
        migrations.AddField(
            model_name='comedor',
            name='fecha_creacion',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.CreateModel(
            name='AuditComedorPrograma',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('changed_at', models.DateTimeField(auto_now_add=True)),
                ('changed_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='comedor_programa_changes', to=settings.AUTH_USER_MODEL)),
                ('comedor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='programa_changes', to='comedores.comedor')),
                ('from_programa', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='programa_changes_from', to='comedores.programas')),
                ('to_programa', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='programa_changes_to', to='comedores.programas')),
            ],
            options={
                'verbose_name': 'Cambio de programa del comedor',
                'verbose_name_plural': 'Cambios de programa del comedor',
                'ordering': ['-changed_at', '-id'],
                'indexes': [models.Index(fields=['comedor', 'changed_at'], name='comedores_a_comedor_c6234f_idx'), models.Index(fields=['changed_by'], name='comedores_a_changed_432a95_idx')],
            },
        ),
        migrations.AddField(
            model_name='comedor',
            name='estado_validacion',
            field=models.CharField(choices=[('Pendiente', 'Pendiente'), ('Validado', 'Validado'), ('No Validado', 'No Validado')], default='Pendiente', max_length=20, verbose_name='Estado de validación'),
        ),
        migrations.AddField(
            model_name='comedor',
            name='fecha_validado',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Fecha de validación'),
        ),
        migrations.CreateModel(
            name='HistorialValidacion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('estado_validacion', models.CharField(choices=[('Pendiente', 'Pendiente'), ('Validado', 'Validado'), ('No Validado', 'No Validado')], max_length=20)),
                ('comentario', models.TextField(verbose_name='Comentario')),
                ('fecha_validacion', models.DateTimeField(auto_now_add=True, verbose_name='Fecha de validación')),
                ('comedor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='historial_validaciones', to='comedores.comedor')),
                ('usuario', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Historial de validación',
                'verbose_name_plural': 'Historiales de validación',
                'ordering': ['-fecha_validacion'],
                'indexes': [models.Index(fields=['comedor', 'fecha_validacion'], name='comedores_h_comedor_b8b8c8_idx')],
            },
        ),
        migrations.RenameIndex(
            model_name='historialvalidacion',
            new_name='comedores_h_comedor_86d7a4_idx',
            old_name='comedores_h_comedor_b8b8c8_idx',
        ),
        migrations.CreateModel(
            name='EstadoActividad',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('estado', models.CharField(max_length=255)),
            ],
            options={
                'verbose_name': 'Estado de Actividad',
                'verbose_name_plural': 'Estados de Actividad',
                'ordering': ['id'],
            },
        ),
        migrations.CreateModel(
            name='EstadoProceso',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('estado', models.CharField(max_length=255)),
                ('estado_actividad', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='comedores.estadoactividad')),
            ],
            options={
                'verbose_name': 'Estado de Proceso',
                'verbose_name_plural': 'Estados de Proceso',
                'ordering': ['id'],
            },
        ),
        migrations.CreateModel(
            name='EstadoDetalle',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('estado', models.CharField(max_length=255)),
                ('estado_proceso', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='comedores.estadoproceso')),
            ],
            options={
                'verbose_name': 'Estado de Detalle',
                'verbose_name_plural': 'Estados de Detalle',
                'ordering': ['id'],
            },
        ),
        migrations.CreateModel(
            name='EstadoGeneral',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('estado_actividad', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='comedores.estadoactividad')),
                ('estado_proceso', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='comedores.estadoproceso')),
                ('estado_detalle', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='comedores.estadodetalle')),
            ],
        ),
        migrations.CreateModel(
            name='EstadoHistorial',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fecha_cambio', models.DateTimeField(auto_now_add=True)),
                ('comedor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='historial_estados', to='comedores.comedor')),
                ('estado_general', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='comedores.estadogeneral')),
                ('usuario', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Historial de Estado de Comedor',
                'verbose_name_plural': 'Historiales de Estado de Comedor',
                'ordering': ['-fecha_cambio'],
            },
        ),
        migrations.AddField(
            model_name='comedor',
            name='ultimo_estado',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='comedores_con_ultimo_estado', to='comedores.estadohistorial'),
        ),
        migrations.RunPython(
            code=crear_historial_inicial,
            reverse_code=migrations.RunPython.noop,
        ),
        migrations.RemoveField(
            model_name='comedor',
            name='estado_general',
        ),
        migrations.AlterField(
            model_name='comedor',
            name='estado_validacion',
            field=models.CharField(blank=True, choices=[('Pendiente', 'Pendiente'), ('Validado', 'Validado'), ('No Validado', 'No Validado')], default='Pendiente', max_length=20, verbose_name='Estado de validación'),
        ),
        migrations.AddField(
            model_name='historialvalidacion',
            name='opciones_no_validar',
            field=models.JSONField(blank=True, help_text='Opciones seleccionadas cuando se marca como no validado', null=True, verbose_name='Opciones de no validación'),
        ),
        migrations.AlterField(
            model_name='historialvalidacion',
            name='comentario',
            field=models.TextField(blank=True, null=True, verbose_name='Comentario'),
        ),
        migrations.AddField(
            model_name='nomina',
            name='estado_nuevo',
            field=models.CharField(choices=[('pendiente', 'Pendiente'), ('activo', 'Activo'), ('baja', 'Baja')], default='pendiente', max_length=20),
        ),
        migrations.RunPython(
            code=copy_estado_forward,
            reverse_code=copy_estado_backward,
        ),
        migrations.RemoveField(
            model_name='nomina',
            name='estado',
        ),
        migrations.RenameField(
            model_name='nomina',
            old_name='estado_nuevo',
            new_name='estado',
        ),
        migrations.AlterField(
            model_name='comedor',
            name='comienzo',
            field=models.IntegerField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(1900), django.core.validators.MaxValueValidator(2026)], verbose_name='Año en el que comenzó a funcionar'),
        ),
        migrations.AlterField(
            model_name='nomina',
            name='estado',
            field=models.CharField(choices=[('activo', 'Activo'), ('pendiente', 'Pendiente'), ('baja', 'Baja')], default='pendiente', max_length=20),
        ),
        migrations.AlterField(
            model_name='referente',
            name='mail',
            field=core.fields.UnicodeEmailField(blank=True, max_length=254, null=True, verbose_name='Mail del referente'),
        ),
        migrations.AlterModelManagers(
            name='comedor',
            managers=[
                ('objects', core.soft_delete.base.SoftDeleteManager()),
                ('all_objects', core.soft_delete.base.SoftDeleteManager(include_deleted=True)),
            ],
        ),
        migrations.AlterModelManagers(
            name='nomina',
            managers=[
                ('objects', core.soft_delete.base.SoftDeleteManager()),
                ('all_objects', core.soft_delete.base.SoftDeleteManager(include_deleted=True)),
            ],
        ),
        migrations.AlterModelManagers(
            name='observacion',
            managers=[
                ('objects', core.soft_delete.base.SoftDeleteManager()),
                ('all_objects', core.soft_delete.base.SoftDeleteManager(include_deleted=True)),
            ],
        ),
        migrations.AddField(
            model_name='comedor',
            name='deleted_at',
            field=models.DateTimeField(blank=True, db_index=True, null=True),
        ),
        migrations.AddField(
            model_name='comedor',
            name='deleted_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='nomina',
            name='deleted_at',
            field=models.DateTimeField(blank=True, db_index=True, null=True),
        ),
        migrations.AddField(
            model_name='nomina',
            name='deleted_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='observacion',
            name='deleted_at',
            field=models.DateTimeField(blank=True, db_index=True, null=True),
        ),
        migrations.AddField(
            model_name='observacion',
            name='deleted_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL),
        ),
    ]
