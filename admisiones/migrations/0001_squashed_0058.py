import core.soft_delete.base
from decimal import Decimal
from django.conf import settings
import django.core.validators
from django.db import migrations, models
from django.db.models import F
import django.db.models.deletion


def remove_documentacion_tipo_if_exists(apps, schema_editor):
    if schema_editor.connection.vendor != "mysql":
        return
    with schema_editor.connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME = 'admisiones_documentacion'
              AND COLUMN_NAME = 'tipo_id'
            """
        )
        exists = cursor.fetchone()[0] > 0
        if not exists:
            return
        cursor.execute(
            """
            SELECT CONSTRAINT_NAME
            FROM information_schema.KEY_COLUMN_USAGE
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME = 'admisiones_documentacion'
              AND COLUMN_NAME = 'tipo_id'
              AND REFERENCED_TABLE_NAME IS NOT NULL
            """
        )
        fk_result = cursor.fetchone()
        if fk_result:
            cursor.execute(
                f"ALTER TABLE `admisiones_documentacion` DROP FOREIGN KEY `{fk_result[0]}`"
            )
        cursor.execute(
            """
            SELECT INDEX_NAME
            FROM information_schema.STATISTICS
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME = 'admisiones_documentacion'
              AND COLUMN_NAME = 'tipo_id'
              AND INDEX_NAME != 'PRIMARY'
            """
        )
        for (index_name,) in cursor.fetchall():
            cursor.execute(
                f"ALTER TABLE `admisiones_documentacion` DROP INDEX `{index_name}`"
            )
        cursor.execute("ALTER TABLE `admisiones_documentacion` DROP COLUMN `tipo_id`")


def update_estado_mostrar(apps, schema_editor):
    Admision = apps.get_model("admisiones", "Admision")
    Admision.objects.filter(estado_mostrar="Documentación finalizada").update(
        estado_mostrar="Documentación cargada"
    )


def reverse_update_estado_mostrar(apps, schema_editor):
    Admision = apps.get_model("admisiones", "Admision")
    Admision.objects.filter(estado_mostrar="Documentación cargada").update(
        estado_mostrar="Documentación finalizada"
    )


def update_documentacion_aval_labels(apps, schema_editor):
    Documentacion = apps.get_model("admisiones", "Documentacion")
    renames = {
        "DNI Autoridad Máxima - Aval 1": "DNI Autoridad Máxima Aval 1- DNI Aval 1 (persona física)",
        "DNI Autoridad Máxima Aval 1": "DNI Autoridad Máxima Aval 1- DNI Aval 1 (persona física)",
        "DNI Autoridad Máxima - Aval 2": "DNI Autoridad Máxima Aval 2 - DNI Aval 2 (persona física)",
        "DNI Autoridad Máxima Aval 2": "DNI Autoridad Máxima Aval 2 - DNI Aval 2 (persona física)",
        "Acta Designación - Aval 1": "Acta Designación Aval 1 - Designación de cargo Aval 1 (persona física)",
        "Acta Designación Aval 1": "Acta Designación Aval 1 - Designación de cargo Aval 1 (persona física)",
        "Acta Designación - Aval 2": "Acta Designación Aval 2 - Designación de cargo Aval 2 (persona física)",
        "Acta Designación Aval 2": "Acta Designación Aval 2 - Designación de cargo Aval 2 (persona física)",
        "Aval 1": "Nota Aval 1",
        "Aval 2": "Nota Aval 2",
    }
    for old_name, new_name in renames.items():
        Documentacion.objects.filter(nombre=old_name).update(nombre=new_name)
    optional_names = [
        "Acta constitutiva - Aval 1",
        "Acta constitutiva Aval 1",
        "Acta constitutiva - Aval 2",
        "Acta constitutiva Aval 2",
        "Estatuto - Aval 1",
        "Estatuto Aval 1",
        "Estatuto - Aval 2",
        "Estatuto Aval 2",
        "Reso Personería Jurídica - Aval 1",
        "Reso Personería Jurídica Aval 1",
        "Reso Personería Jurídica - Aval 2",
        "Reso Personería Jurídica Aval 2",
    ]
    Documentacion.objects.filter(nombre__in=optional_names).update(obligatorio=False)


def cap_montos(apps, schema_editor):
    informe_tecnico = apps.get_model("admisiones", "InformeTecnico")
    max_value = 99_000_000
    fields = ("monto_1", "monto_2", "monto_3", "monto_4", "monto_5", "monto_6")
    for field in fields:
        informe_tecnico.objects.filter(**{f"{field}__gt": max_value}).update(
            **{field: max_value}
        )


MEALS = ["desayuno", "almuerzo", "merienda", "cena"]
DAYS = ["lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo"]


def backfill_informetecnico_ultimo_convenio(apps, schema_editor):
    InformeTecnico = apps.get_model("admisiones", "InformeTecnico")
    update_kwargs = {}
    for meal in MEALS:
        for day in DAYS:
            update_kwargs[f"aprobadas_ultimo_convenio_{meal}_{day}"] = F(
                f"aprobadas_{meal}_{day}"
            )
    InformeTecnico.objects.filter(admision__tipo="renovacion").update(**update_kwargs)

class Migration(migrations.Migration):

    replaces = [('admisiones', '0001_initial'), ('admisiones', '0002_anexo_campoasubsanar_formularioproyectodisposicion_and_more'), ('admisiones', '0003_admision_enviado_acompaniamiento'), ('admisiones', '0004_informecomplementario_informecomplementariocampos'), ('admisiones', '0005_informetecnico_fecha_vencimiento_mandatos'), ('admisiones', '0006_informetecnico_conclusiones'), ('admisiones', '0007_anexo_barrio_squashed_0008_alter_anexo_barrio'), ('admisiones', '0007_alter_informetecnico_conclusiones'), ('admisiones', '0009_merge_20250911_1218'), ('admisiones', '0007_archivoadmision_numero_gde'), ('admisiones', '0008_merge_20250911_1251'), ('admisiones', '0010_merge_20250912_1246'), ('admisiones', '0011_alter_anexo_barrio_alter_archivoadmision_estado'), ('admisiones', '0012_remove_documentacion_tipo_admision_archivo_convenio_and_more'), ('admisiones', '0013_alter_admision_comedor'), ('admisiones', '0014_squashed_0020_complementary_flow'), ('admisiones', '0021_alter_admision_estado_legales'), ('admisiones', '0022_admision_tipo'), ('admisiones', '0023_informetecnico_monto_1_informetecnico_monto_2_and_more'), ('admisiones', '0024_informetecnico_responsable_tarjeta_cuit'), ('admisiones', '0025_informetecnico_domicilio_electronico_espacio_and_more'), ('admisiones', '0026_archivoadmision_motivo_descarte_expediente'), ('admisiones', '0027_remove_archivoadmision_motivo_descarte_expediente_and_more'), ('admisiones', '0028_admision_fecha_descarte_expediente_and_more'), ('admisiones', '0029_remove_informetecnico_responsable_admin_apellido_and_more'), ('admisiones', '0030_admision_numero_if_tecnico'), ('admisiones', '0031_alter_admision_numero_if_tecnico'), ('admisiones', '0032_archivoadmision_orden'), ('admisiones', '0033_remove_archivoadmision_orden_documentacion_orden'), ('admisiones', '0034_admision_estado_admision'), ('admisiones', '0035_admision_activa'), ('admisiones', '0036_alter_admision_estado_admision'), ('admisiones', '0037_admision_motivo_forzar_cierre_and_more'), ('admisiones', '0038_admision_estado_mostrar_and_more'), ('admisiones', '0039_alter_admision_estado_admision_and_more'), ('admisiones', '0040_update_documentacion_finalizada_display'), ('admisiones', '0041_alter_admision_estado_admision'), ('admisiones', '0042_archivoadmision_creado_por_and_more'), ('admisiones', '0043_alter_admision_estado_legales'), ('admisiones', '0044_alter_informetecnico_creado_por_and_more'), ('admisiones', '0045_update_documentacion_aval_labels'), ('admisiones', '0046_alter_informetecnico_montos_decimal'), ('admisiones', '0047_informetecnico_no_corresponde_fecha_vencimiento'), ('admisiones', '0048_admision_convenio_numero'), ('admisiones', '0049_informetecnico_prestaciones_ultimo_convenio'), ('admisiones', '0050_backfill_informetecnico_ultimo_convenio'), ('admisiones', '0048_make_validacion_registro_nacional_optional'), ('admisiones', '0051_merge_20260120_1622'), ('admisiones', '0052_informe_tecnico_docx_workflow'), ('admisiones', '0053_alter_admision_estado_admision'), ('admisiones', '0054_admision_archivo_informe_tecnico_gde'), ('admisiones', '0055_update_docx_editado_display_label'), ('admisiones', '0056_alter_informetecnico_estado'), ('admisiones', '0057_alter_archivoadmision_managers_and_more'), ('admisiones', '0058_alter_admision_estado_admision')]

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("comedores", "0001_squashed_0023"),
    ]

    operations = [
        migrations.CreateModel(
            name='Admision',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('num_expediente', models.CharField(blank=True, max_length=255, null=True)),
                ('num_if', models.CharField(blank=True, max_length=100, null=True)),
                ('legales_num_if', models.CharField(blank=True, max_length=100, null=True)),
                ('creado', models.DateField(auto_now_add=True, null=True)),
                ('modificado', models.DateField(auto_now=True, null=True)),
                ('enviado_legales', models.BooleanField(default=False, verbose_name='¿Enviado a legales?')),
                ('estado_legales', models.CharField(blank=True, choices=[('A Rectificar', 'A Rectificar'), ('Rectificado', 'Rectificado'), ('Pendiente de Validacion', 'Pendiente de Validacion'), ('Informe SGA Generado', 'Informe SGA Generado'), ('Resolucion Generada', 'Resolucion Generada'), ('Convenio Firmado', 'Convenio Firmado'), ('Finalizado', 'Finalizado')], max_length=40, null=True, verbose_name='Estado')),
                ('observaciones', models.TextField(blank=True, null=True, verbose_name='Observaciones')),
                ('comedor', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='comedores.comedor')),
            ],
            options={
                'verbose_name': 'admisiontecnico',
                'verbose_name_plural': 'admisionestecnicos',
                'ordering': ['-creado'],
            },
        ),
        migrations.CreateModel(
            name='TipoDocumentacion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=255, unique=True)),
                ('descripcion', models.CharField(blank=True, max_length=255, null=True)),
            ],
            options={
                'verbose_name': 'Tipo de Documentación',
                'verbose_name_plural': 'Tipos de Documentación',
                'ordering': ['nombre'],
            },
        ),
        migrations.CreateModel(
            name='TipoConvenio',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=255)),
            ],
            options={
                'verbose_name': 'tipoconvenio',
                'verbose_name_plural': 'tiposconvenios',
                'indexes': [models.Index(fields=['nombre'], name='admisiones__nombre_bdabcc_idx')],
            },
        ),
        migrations.CreateModel(
            name='InformeTecnicoPDF',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tipo', models.CharField(choices=[('base', 'Base'), ('juridico', 'Jurídico')], max_length=20)),
                ('informe_id', models.PositiveIntegerField()),
                ('archivo', models.FileField(upload_to='informes_tecnicos/')),
                ('creado', models.DateTimeField(auto_now_add=True)),
                ('admision', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='informe_pdf', to='admisiones.admision')),
                ('comedor', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='comedores.comedor')),
            ],
        ),
        migrations.CreateModel(
            name='InformeTecnicoJuridico',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('expediente_nro', models.CharField(max_length=100, verbose_name='Expediente Nro.')),
                ('nombre_org', models.CharField(max_length=255, verbose_name='Nombre de la Organización Solicitante')),
                ('domicilio_org', models.CharField(max_length=255, verbose_name='Domicilio de la Organización Solicitante')),
                ('localidad_org', models.CharField(max_length=255, verbose_name='Localidad de la Organización Solicitante')),
                ('partido_org', models.CharField(max_length=255, verbose_name='Partido de la Organización Solicitante')),
                ('provincia_org', models.CharField(max_length=255, verbose_name='Provincia de la Organización Solicitante')),
                ('telefono_org', models.CharField(max_length=50, verbose_name='Teléfono de la Organización Solicitante')),
                ('mail_org', models.EmailField(max_length=254, verbose_name='Mail de la Organización Solicitante')),
                ('cuit_org', models.CharField(max_length=20, verbose_name='CUIT de la Organización Solicitante')),
                ('representante_nombre', models.CharField(max_length=255, verbose_name='Nombre y Apellido del Representante')),
                ('representante_cargo', models.CharField(max_length=100, verbose_name='Cargo del Representante')),
                ('representante_dni', models.CharField(max_length=20, verbose_name='DNI del Representante')),
                ('tipo_espacio', models.CharField(choices=[('Comedor', 'Comedor'), ('Merendero', 'Merendero')], max_length=50, verbose_name='Tipo de Espacio Comunitario')),
                ('nombre_espacio', models.CharField(max_length=255, verbose_name='Nombre del Comedor/Merendero')),
                ('domicilio_espacio', models.CharField(max_length=255, verbose_name='Domicilio del Comedor/Merendero')),
                ('barrio_espacio', models.CharField(max_length=255, verbose_name='Barrio del Comedor/Merendero')),
                ('localidad_espacio', models.CharField(max_length=255, verbose_name='Localidad del Comedor/Merendero')),
                ('partido_espacio', models.CharField(max_length=255, verbose_name='Partido del Comedor/Merendero')),
                ('provincia_espacio', models.CharField(max_length=255, verbose_name='Provincia del Comedor/Merendero')),
                ('responsable_tarjeta_nombre', models.CharField(max_length=255, verbose_name='Nombre del Responsable de la Tarjeta')),
                ('responsable_tarjeta_dni', models.CharField(max_length=20, verbose_name='DNI del Responsable de la Tarjeta')),
                ('responsable_tarjeta_domicilio', models.CharField(max_length=255, verbose_name='Domicilio del Responsable de la Tarjeta')),
                ('responsable_tarjeta_localidad', models.CharField(max_length=255, verbose_name='Localidad del Responsable de la Tarjeta')),
                ('responsable_tarjeta_provincia', models.CharField(max_length=255, verbose_name='Provincia del Responsable de la Tarjeta')),
                ('responsable_tarjeta_telefono', models.CharField(max_length=50, verbose_name='Teléfono del Responsable de la Tarjeta')),
                ('responsable_tarjeta_mail', models.EmailField(max_length=254, verbose_name='Mail del Responsable de la Tarjeta')),
                ('nota_gde_if', models.CharField(max_length=255, verbose_name='Nota GDE IF')),
                ('personas_desayuno_letras', models.CharField(max_length=255, verbose_name='Cantidad Personas Desayuno (en letras)')),
                ('dias_desayuno_letras', models.CharField(max_length=255, verbose_name='Cantidad Días Desayuno (en letras)')),
                ('personas_almuerzo_letras', models.CharField(max_length=255, verbose_name='Cantidad Personas Almuerzo (en letras)')),
                ('dias_almuerzo_letras', models.CharField(max_length=255, verbose_name='Cantidad Días Almuerzo (en letras)')),
                ('personas_merienda_letras', models.CharField(max_length=255, verbose_name='Cantidad Personas Merienda (en letras)')),
                ('dias_merienda_letras', models.CharField(max_length=255, verbose_name='Cantidad Días Merienda (en letras)')),
                ('personas_cena_letras', models.CharField(max_length=255, verbose_name='Cantidad Personas Cena (en letras)')),
                ('dias_cena_letras', models.CharField(max_length=255, verbose_name='Cantidad Días Cena (en letras)')),
                ('constancia_subsidios_dnsa', models.CharField(max_length=255, verbose_name='Constancia IF RTA DNSA sobre subsidios')),
                ('constancia_subsidios_pnud', models.CharField(max_length=255, verbose_name='Constancia IF RTA PNUD sobre subsidios')),
                ('validacion_rncm_if', models.CharField(max_length=255, verbose_name='Validación Registro Nacional Comedores/Merenderos (IF)')),
                ('partido_destinataria', models.CharField(max_length=255, verbose_name='Partido donde se ubica la población destinataria')),
                ('provincia_destinataria', models.CharField(max_length=255, verbose_name='Provincia donde se ubica la población destinataria')),
                ('if_relevamiento', models.CharField(max_length=255, verbose_name='IF de relevamiento territorial')),
                ('prestaciones_aprobadas_desayuno', models.IntegerField(default=0, verbose_name='Cantidad de prestaciones aprobadas Desayuno (Lunes a Domingo)')),
                ('prestaciones_aprobadas_almuerzo', models.IntegerField(default=0, verbose_name='Cantidad de prestaciones aprobadas Almuerzo (Lunes a Domingo)')),
                ('prestaciones_aprobadas_merienda', models.IntegerField(default=0, verbose_name='Cantidad de prestaciones aprobadas Merienda (Lunes a Domingo)')),
                ('prestaciones_aprobadas_cena', models.IntegerField(default=0, verbose_name='Cantidad de prestaciones aprobadas Cena (Lunes a Domingo)')),
                ('estado', models.CharField(choices=[('Para revision', 'Para revisión'), ('Validado', 'Validado'), ('A subsanar', 'A subsanar')], default='Para revision', max_length=20, verbose_name='Estado del Informe')),
                ('admision', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='admisiones.admision')),
            ],
        ),
        migrations.CreateModel(
            name='InformeTecnicoBase',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('expediente_nro', models.CharField(max_length=100)),
                ('nombre_org', models.CharField(max_length=255, verbose_name='Nombre de la Organización Solicitante')),
                ('domicilio_org', models.CharField(max_length=255, verbose_name='Domicilio de la Organización Solicitante')),
                ('localidad_org', models.CharField(max_length=255, verbose_name='Localidad de la Organización Solicitante')),
                ('partido_org', models.CharField(max_length=255, verbose_name='Partido de la Organización Solicitante')),
                ('provincia_org', models.CharField(max_length=255, verbose_name='Provincia de la Organización Solicitante')),
                ('telefono_org', models.CharField(max_length=50, verbose_name='Teléfono de la Organización Solicitante')),
                ('mail_org', models.EmailField(max_length=254, verbose_name='Mail de la Organización Solicitante')),
                ('cuit_org', models.CharField(max_length=20, verbose_name='CUIT de la Organización Solicitante')),
                ('representante_nombre', models.CharField(max_length=255, verbose_name='Nombre y Apellido del Representante')),
                ('representante_cargo', models.CharField(max_length=100, verbose_name='Cargo del Representante')),
                ('representante_dni', models.CharField(max_length=20, verbose_name='DNI del Representante')),
                ('tipo_espacio', models.CharField(choices=[('Comedor', 'Comedor'), ('Merendero', 'Merendero')], max_length=50, verbose_name='Tipo de Espacio Comunitario')),
                ('nombre_espacio', models.CharField(max_length=255, verbose_name='Nombre del Comedor/Merendero')),
                ('domicilio_espacio', models.CharField(max_length=255, verbose_name='Domicilio del Comedor/Merendero')),
                ('barrio_espacio', models.CharField(max_length=255, verbose_name='Barrio del Comedor/Merendero')),
                ('localidad_espacio', models.CharField(max_length=255, verbose_name='Localidad del Comedor/Merendero')),
                ('partido_espacio', models.CharField(max_length=255, verbose_name='Partido del Comedor/Merendero')),
                ('provincia_espacio', models.CharField(max_length=255, verbose_name='Provincia del Comedor/Merendero')),
                ('responsable_tarjeta_nombre', models.CharField(max_length=255, verbose_name='Nombre del Responsable de la Tarjeta')),
                ('responsable_tarjeta_dni', models.CharField(max_length=20, verbose_name='DNI del Responsable de la Tarjeta')),
                ('responsable_tarjeta_domicilio', models.CharField(max_length=255, verbose_name='Domicilio del Responsable')),
                ('responsable_tarjeta_localidad', models.CharField(max_length=255, verbose_name='Localidad del Responsable')),
                ('responsable_tarjeta_provincia', models.CharField(max_length=255, verbose_name='Provincia del Responsable')),
                ('responsable_tarjeta_telefono', models.CharField(max_length=50, verbose_name='Teléfono del Responsable')),
                ('responsable_tarjeta_mail', models.EmailField(max_length=254, verbose_name='Mail del Responsable')),
                ('declaracion_jurada', models.CharField(max_length=255, verbose_name='Declaración Jurada sobre recepción de subsidios nacionales')),
                ('constancia_inexistencia_subsidios', models.CharField(max_length=255, verbose_name='Constancia de inexistencia de percepción de otros subsidios nacionales')),
                ('organizacion_avalista_1', models.CharField(max_length=255, verbose_name='Organización Avalista 1')),
                ('organizacion_avalista_2', models.CharField(max_length=255, verbose_name='Organización Avalista 2')),
                ('material_difusion', models.TextField(blank=True, null=True, verbose_name='Material de difusión vinculado')),
                ('prestaciones_desayuno', models.IntegerField(default=0, verbose_name='Cantidad de Prestaciones Mensuales Desayuno')),
                ('prestaciones_almuerzo', models.IntegerField(default=0, verbose_name='Cantidad de Prestaciones Mensuales Almuerzo')),
                ('prestaciones_merienda', models.IntegerField(default=0, verbose_name='Cantidad de Prestaciones Mensuales Merienda')),
                ('prestaciones_cena', models.IntegerField(default=0, verbose_name='Cantidad de Prestaciones Mensuales Cena')),
                ('prestaciones_totales', models.IntegerField(default=0, verbose_name='Total Mensual de Prestaciones')),
                ('estado', models.CharField(choices=[('Para revision', 'Para revisión'), ('Validado', 'Validado'), ('A subsanar', 'A subsanar')], default='Para revision', max_length=20, verbose_name='Estado de la Solicitud')),
                ('admision', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='admisiones.admision')),
            ],
        ),
        migrations.CreateModel(
            name='FormularioRESO',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('pregunta1', models.CharField(blank=True, max_length=255, null=True)),
                ('pregunta2', models.CharField(blank=True, max_length=255, null=True)),
                ('pregunta3', models.CharField(blank=True, max_length=255, null=True)),
                ('creado', models.DateTimeField(auto_now_add=True)),
                ('admision', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='formularios_reso', to='admisiones.admision')),
                ('creado_por', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='FormularioProyectoDeConvenio',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('pregunta1', models.CharField(blank=True, max_length=255, null=True)),
                ('pregunta2', models.CharField(blank=True, max_length=255, null=True)),
                ('pregunta3', models.CharField(blank=True, max_length=255, null=True)),
                ('creado', models.DateTimeField(auto_now_add=True)),
                ('admision', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='formularios_proyecto_convenio', to='admisiones.admision')),
                ('creado_por', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='EstadoAdmision',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=15)),
            ],
            options={
                'verbose_name': 'estadosadmision',
                'verbose_name_plural': 'estadosadmisiones',
                'indexes': [models.Index(fields=['nombre'], name='admisiones__nombre_bcd423_idx')],
            },
        ),
        migrations.CreateModel(
            name='DocumentosExpediente',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(blank=True, max_length=255, null=True)),
                ('tipo', models.CharField(blank=True, max_length=255, null=True)),
                ('value', models.CharField(blank=True, max_length=255, null=True)),
                ('archivo', models.FileField(blank=True, null=True, upload_to='comedor/admisiones_archivos/expediente')),
                ('rectificar', models.BooleanField(default=False, verbose_name='Rectificar')),
                ('observaciones', models.TextField(blank=True, null=True, verbose_name='Observaciones')),
                ('num_if', models.CharField(blank=True, max_length=100, null=True)),
                ('creado', models.DateField(auto_now_add=True, null=True)),
                ('admision', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='admisiones.admision')),
            ],
        ),
        migrations.CreateModel(
            name='Documentacion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=255)),
                ('convenios', models.ManyToManyField(blank=True, to='admisiones.tipoconvenio')),
                ('tipo', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='admisiones.tipodocumentacion')),
            ],
        ),
        migrations.CreateModel(
            name='ArchivoAdmision',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('archivo', models.FileField(blank=True, null=True, upload_to='comedor/admisiones_archivos/')),
                ('estado', models.CharField(choices=[('pendiente', 'Pendiente'), ('validar', 'A Validar'), ('A Validar Abogado', 'A Validar Abogado'), ('Rectificar', 'Rectificar')], default='pendiente', max_length=20)),
                ('rectificar', models.BooleanField(default=False, verbose_name='Rectificar')),
                ('observaciones', models.TextField(blank=True, null=True, verbose_name='Observaciones')),
                ('num_if', models.CharField(blank=True, max_length=100, null=True)),
                ('creado', models.DateField(auto_now_add=True, null=True)),
                ('modificado', models.DateField(auto_now=True, null=True)),
                ('admision', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='admisiones.admision')),
                ('documentacion', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='admisiones.documentacion')),
            ],
        ),
        migrations.CreateModel(
            name='AdmisionHistorial',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('campo', models.CharField(max_length=50)),
                ('valor_anterior', models.TextField(blank=True, null=True)),
                ('valor_nuevo', models.TextField(blank=True, null=True)),
                ('fecha', models.DateTimeField(auto_now_add=True)),
                ('admision', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='historial', to='admisiones.admision')),
                ('usuario', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='admision',
            name='estado',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='admisiones.estadoadmision'),
        ),
        migrations.AddField(
            model_name='admision',
            name='tipo_convenio',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='admisiones.tipoconvenio'),
        ),
        migrations.AddIndex(
            model_name='admision',
            index=models.Index(fields=['comedor'], name='admisiones__comedor_1d8f2b_idx'),
        ),
        migrations.CreateModel(
            name='Anexo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('expediente', models.CharField(blank=True, max_length=100, null=True, verbose_name='Expediente')),
                ('efector', models.CharField(blank=True, max_length=100, null=True, verbose_name='Efector (nombre)')),
                ('tipo_espacio', models.CharField(blank=True, choices=[('Comedor', 'Comedor'), ('Merendero', 'Merendero'), ('Comedor y Merendero', 'Comedor y Merendero')], max_length=50, null=True, verbose_name='Tipo (Comedor / Merendero)')),
                ('domicilio', models.CharField(blank=True, max_length=150, null=True, verbose_name='Domicilio')),
                ('mail', models.EmailField(blank=True, max_length=254, null=True, verbose_name='Correo Electrónico')),
                ('responsable_apellido', models.CharField(blank=True, max_length=150, null=True, verbose_name='Apellido')),
                ('responsable_nombre', models.CharField(blank=True, max_length=150, null=True, verbose_name='Nombre')),
                ('responsable_cuit', models.BigIntegerField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(10000000000), django.core.validators.MaxValueValidator(99999999999)], verbose_name='CUIT / CUIL')),
                ('responsable_domicilio', models.CharField(blank=True, max_length=150, null=True, verbose_name='Domicilio')),
                ('responsable_mail', models.EmailField(blank=True, max_length=254, null=True, verbose_name='Correo Electrónico')),
                ('total_acreditaciones', models.CharField(blank=True, max_length=150, null=True, verbose_name='Total de acreditaciones a Producir')),
                ('plazo_ejecucion', models.CharField(blank=True, max_length=150, null=True, verbose_name='Plazo de Ejecución')),
                ('desayuno_lunes', models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)])),
                ('desayuno_martes', models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)])),
                ('desayuno_miercoles', models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)])),
                ('desayuno_jueves', models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)])),
                ('desayuno_viernes', models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)])),
                ('desayuno_sabado', models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)])),
                ('desayuno_domingo', models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)])),
                ('almuerzo_lunes', models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)])),
                ('almuerzo_martes', models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)])),
                ('almuerzo_miercoles', models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)])),
                ('almuerzo_jueves', models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)])),
                ('almuerzo_viernes', models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)])),
                ('almuerzo_sabado', models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)])),
                ('almuerzo_domingo', models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)])),
                ('merienda_lunes', models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)])),
                ('merienda_martes', models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)])),
                ('merienda_miercoles', models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)])),
                ('merienda_jueves', models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)])),
                ('merienda_viernes', models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)])),
                ('merienda_sabado', models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)])),
                ('merienda_domingo', models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)])),
                ('cena_lunes', models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)])),
                ('cena_martes', models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)])),
                ('cena_miercoles', models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)])),
                ('cena_jueves', models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)])),
                ('cena_viernes', models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)])),
                ('cena_sabado', models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)])),
                ('cena_domingo', models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)])),
                ('admision', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='admisiones.admision')),
                ('barrio', models.CharField(blank=True, max_length=50, null=True, verbose_name='Barrio')),
            ],
        ),
        migrations.CreateModel(
            name='CampoASubsanar',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('campo', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='FormularioProyectoDisposicion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tipo', models.CharField(choices=[('incorporacion', 'Incorporación'), ('renovacion', 'Renovación')], max_length=20)),
                ('archivo', models.FileField(null=True, upload_to='admisiones/formularios_disposicion/')),
                ('creado', models.DateTimeField(auto_now_add=True)),
                ('admision', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='proyecto_disposicion', to='admisiones.admision')),
                ('creado_por', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='InformeTecnico',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tipo', models.CharField(choices=[('base', 'Base'), ('juridico', 'Jurídico')], max_length=20)),
                ('expediente_nro', models.CharField(max_length=100, verbose_name='Número Expediente')),
                ('nombre_organizacion', models.CharField(max_length=255, verbose_name='Nombre de la Organización Solicitante')),
                ('domicilio_organizacion', models.CharField(max_length=255, verbose_name='Domicilio de la Organización Solicitante')),
                ('localidad_organizacion', models.CharField(max_length=255, verbose_name='Localidad de la Organización Solicitante')),
                ('partido_organizacion', models.CharField(max_length=255, verbose_name='Partido de la Organización Solicitante')),
                ('provincia_organizacion', models.CharField(max_length=255, verbose_name='Provincia de la Organización Solicitante')),
                ('telefono_organizacion', models.CharField(max_length=50, verbose_name='Teléfono de la Organización Solicitante')),
                ('mail_organizacion', models.EmailField(max_length=254, verbose_name='Mail de la Organización Solicitante')),
                ('cuit_organizacion', models.CharField(max_length=20, verbose_name='CUIT de la Organización Solicitante')),
                ('representante_nombre', models.CharField(max_length=255, verbose_name='Nombre y Apellido del Representante')),
                ('representante_cargo', models.CharField(max_length=100, verbose_name='Cargo del Representante')),
                ('representante_dni', models.CharField(max_length=20, verbose_name='DNI del Representante')),
                ('tipo_espacio', models.CharField(choices=[('Comedor', 'Comedor'), ('Merendero', 'Merendero'), ('Comedor y Merendero', 'Comedor y Merendero')], max_length=50, verbose_name='Tipo de Espacio Comunitario')),
                ('nombre_espacio', models.CharField(max_length=255, verbose_name='Nombre del Comedor/Merendero')),
                ('domicilio_espacio', models.CharField(max_length=255, verbose_name='Domicilio del Comedor/Merendero')),
                ('barrio_espacio', models.CharField(max_length=255, verbose_name='Barrio del Comedor/Merendero')),
                ('localidad_espacio', models.CharField(max_length=255, verbose_name='Localidad del Comedor/Merendero')),
                ('partido_espacio', models.CharField(max_length=255, verbose_name='Partido del Comedor/Merendero')),
                ('provincia_espacio', models.CharField(max_length=255, verbose_name='Provincia del Comedor/Merendero')),
                ('responsable_tarjeta_nombre', models.CharField(max_length=255, verbose_name='Nombre del Responsable de la Tarjeta')),
                ('responsable_tarjeta_dni', models.CharField(max_length=20, verbose_name='DNI del Responsable de la Tarjeta')),
                ('responsable_tarjeta_domicilio', models.CharField(max_length=255, verbose_name='Domicilio del Responsable de la Tarjeta')),
                ('responsable_tarjeta_localidad', models.CharField(max_length=255, verbose_name='Localidad del Responsable de la Tarjeta')),
                ('responsable_tarjeta_provincia', models.CharField(max_length=255, verbose_name='Provincia del Responsable de la Tarjeta')),
                ('responsable_tarjeta_telefono', models.CharField(max_length=50, verbose_name='Teléfono del Responsable de la Tarjeta')),
                ('responsable_tarjeta_mail', models.EmailField(max_length=254, verbose_name='Mail del Responsable de la Tarjeta')),
                ('nota_gde_if', models.CharField(max_length=255, verbose_name='Nota GDE IF')),
                ('constancia_subsidios_dnsa', models.CharField(max_length=255, verbose_name='Constancia IF RTA DNSA sobre subsidios')),
                ('constancia_subsidios_pnud', models.CharField(max_length=255, verbose_name='Constancia IF RTA PNUD sobre subsidios')),
                ('partido_poblacion_destinataria', models.CharField(max_length=255, verbose_name='Partido donde se ubica la población destinataria')),
                ('provincia_poblacion_destinataria', models.CharField(max_length=255, verbose_name='Provincia donde se ubica la población destinataria')),
                ('prestaciones_desayuno_numero', models.IntegerField(default=0, verbose_name='Cantidad de Prestaciones Semanales Desayuno - En números (Solicitante)')),
                ('prestaciones_almuerzo_numero', models.IntegerField(default=0, verbose_name='Cantidad de Prestaciones Semanales Almuerzo - En números (Solicitante)')),
                ('prestaciones_merienda_numero', models.IntegerField(default=0, verbose_name='Cantidad de Prestaciones Semanales Merienda - En números (Solicitante)')),
                ('prestaciones_cena_numero', models.IntegerField(default=0, verbose_name='Cantidad de Prestaciones Semanales Cena - En números (Solicitante)')),
                ('prestaciones_desayuno_letras', models.CharField(max_length=255, verbose_name='Cantidad de Prestaciones Semanales Desayuno - En letras (Solicitante)')),
                ('prestaciones_almuerzo_letras', models.CharField(max_length=255, verbose_name='Cantidad de Prestaciones Semanales Almuerzo - En letras (Solicitante)')),
                ('prestaciones_merienda_letras', models.CharField(max_length=255, verbose_name='Cantidad de Prestaciones Semanales Merienda - En letras (Solicitante)')),
                ('prestaciones_cena_letras', models.CharField(max_length=255, verbose_name='Cantidad de Prestaciones Semanales Cena - En letras (Solicitante)')),
                ('if_relevamiento', models.CharField(max_length=255, verbose_name='IF de relevamiento territorial')),
                ('declaracion_jurada_recepcion_subsidios', models.CharField(max_length=255, verbose_name='Declaración Jurada sobre recepción de subsidios nacionales')),
                ('constancia_inexistencia_percepcion_otros_subsidios', models.CharField(max_length=255, verbose_name='Constancia de inexistencia de percepción de otros subsidios nacionales')),
                ('organizacion_avalista_1', models.CharField(max_length=255, verbose_name='Organización Avalista 1')),
                ('organizacion_avalista_2', models.CharField(max_length=255, verbose_name='Organización Avalista 2')),
                ('material_difusion_vinculado', models.CharField(max_length=255, verbose_name='Material de difusión vinculado')),
                ('validacion_registro_nacional', models.CharField(max_length=255, verbose_name='Validación Registro Nacional Comedores/Merenderos')),
                ('IF_relevamiento_territorial', models.CharField(max_length=255, verbose_name='IF de relevamiento territorial')),
                ('estado', models.CharField(choices=[('Para revision', 'Para revisión'), ('Validado', 'Validado'), ('A subsanar', 'A subsanar')], default='Para revision', max_length=20, verbose_name='Estado del Informe')),
                ('admision', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='admisiones.admision')),
                ('fecha_vencimiento_mandatos', models.DateField(blank=True, null=True, verbose_name='Fecha de vencimiento de mandatos')),
                ('conclusiones', models.TextField(blank=True, null=True, verbose_name='Aplicación de Criterios')),
            ],
        ),
        migrations.CreateModel(
            name='ObservacionGeneralInforme',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('texto', models.TextField()),
                ('informe', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='admisiones.informetecnico')),
            ],
        ),
        migrations.RemoveField(
            model_name='informetecnicobase',
            name='admision',
        ),
        migrations.RemoveField(
            model_name='informetecnicojuridico',
            name='admision',
        ),
        migrations.RemoveField(
            model_name='formularioproyectodeconvenio',
            name='pregunta1',
        ),
        migrations.RemoveField(
            model_name='formularioproyectodeconvenio',
            name='pregunta2',
        ),
        migrations.RemoveField(
            model_name='formularioproyectodeconvenio',
            name='pregunta3',
        ),
        migrations.AddField(
            model_name='formularioproyectodeconvenio',
            name='archivo',
            field=models.FileField(null=True, upload_to='admisiones/formularios_convenio/'),
        ),
        migrations.AlterField(
            model_name='archivoadmision',
            name='archivo',
            field=models.FileField(blank=True, null=True, upload_to='admisiones/admisiones_archivos/'),
        ),
        migrations.AlterField(
            model_name='documentosexpediente',
            name='archivo',
            field=models.FileField(blank=True, null=True, upload_to='admisiones/expediente'),
        ),
        migrations.AlterField(
            model_name='formularioproyectodeconvenio',
            name='admision',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='proyecto_convenio', to='admisiones.admision'),
        ),
        migrations.AlterField(
            model_name='informetecnicopdf',
            name='archivo',
            field=models.FileField(upload_to='admisiones/informes_tecnicos/'),
        ),
        migrations.DeleteModel(
            name='FormularioRESO',
        ),
        migrations.DeleteModel(
            name='InformeTecnicoBase',
        ),
        migrations.DeleteModel(
            name='InformeTecnicoJuridico',
        ),
        migrations.AddField(
            model_name='campoasubsanar',
            name='informe',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='admisiones.informetecnico'),
        ),
        migrations.AddField(
            model_name='admision',
            name='enviado_acompaniamiento',
            field=models.BooleanField(default=False, verbose_name='¿Enviado a Acompañamiento?'),
        ),
        migrations.CreateModel(
            name='InformeComplementario',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('pdf', models.FileField(null=True, upload_to='admisiones/informes_complementarios/')),
                ('creado', models.DateField(auto_now_add=True, null=True)),
                ('admision', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='admisiones.admision')),
                ('creado_por', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('informe_tecnico', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='admisiones.informetecnico')),
            ],
        ),
        migrations.CreateModel(
            name='InformeComplementarioCampos',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('campo', models.CharField(max_length=255)),
                ('value', models.CharField(max_length=255)),
                ('informe_complementario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='admisiones.informecomplementario')),
            ],
        ),
        migrations.AddField(
            model_name='archivoadmision',
            name='numero_gde',
            field=models.CharField(blank=True, help_text='Número de expediente GDE asignado por el técnico después de la carga en sistema externo', max_length=50, null=True, verbose_name='Número de GDE'),
        ),
        migrations.AlterField(
            model_name='archivoadmision',
            name='estado',
            field=models.CharField(choices=[('pendiente', 'Pendiente'), ('validar', 'A Validar'), ('A Validar Abogado', 'A Validar Abogado'), ('Rectificar', 'Rectificar'), ('Aceptado', 'Aceptado')], default='pendiente', max_length=20),
        ),
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunPython(
                    code=remove_documentacion_tipo_if_exists,
                    reverse_code=migrations.RunPython.noop,
                ),
            ],
            state_operations=[
                migrations.RemoveField(
                    model_name='documentacion',
                    name='tipo',
                ),
            ],
        ),
        migrations.AddField(
            model_name='admision',
            name='archivo_convenio',
            field=models.FileField(blank=True, null=True, upload_to='admisiones/convenios/'),
        ),
        migrations.AddField(
            model_name='admision',
            name='archivo_disposicion',
            field=models.FileField(blank=True, null=True, upload_to='admisiones/disposicion/'),
        ),
        migrations.AddField(
            model_name='admision',
            name='dictamen_motivo',
            field=models.CharField(blank=True, choices=[('observacion en informe técnico', 'Observación en informe técnico'), ('observacion en proyecto de convenio', 'Observación en proyecto de convenio'), ('observacion en proyecto de disposicion', 'Observación en proyecto de disposición')], max_length=40, null=True, verbose_name='Tipo de observación'),
        ),
        migrations.AddField(
            model_name='admision',
            name='enviada_a_archivo',
            field=models.BooleanField(default=False, verbose_name='Enviada a Archivo'),
        ),
        migrations.AddField(
            model_name='admision',
            name='informe_sga',
            field=models.BooleanField(default=False, verbose_name='Estados Informe SGA'),
        ),
        migrations.AddField(
            model_name='admision',
            name='intervencion_juridicos',
            field=models.CharField(blank=True, choices=[('validado', 'Validado'), ('rechazado', 'Rechazado')], max_length=20, null=True, verbose_name='Intervención Jurídicos'),
        ),
        migrations.AddField(
            model_name='admision',
            name='numero_convenio',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='admision',
            name='numero_disposicion',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='admision',
            name='observaciones_informe_tecnico_complementario',
            field=models.TextField(blank=True, null=True, verbose_name='Observaciones informe técnico complementario'),
        ),
        migrations.AddField(
            model_name='admision',
            name='observaciones_reinicio_expediente',
            field=models.TextField(blank=True, null=True, verbose_name='Observaciones reinicio de expediente'),
        ),
        migrations.AddField(
            model_name='admision',
            name='rechazo_juridicos_motivo',
            field=models.CharField(blank=True, choices=[('providencia', 'Por providencia'), ('dictamen', 'Por dictamen')], max_length=40, null=True, verbose_name='Motivo Rechazo Jurídicos'),
        ),
        migrations.AddField(
            model_name='archivoadmision',
            name='nombre_personalizado',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Nombre personalizado'),
        ),
        migrations.AddField(
            model_name='documentacion',
            name='obligatorio',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='formularioproyectodeconvenio',
            name='archivo_docx',
            field=models.FileField(null=True, upload_to='admisiones/formularios_convenio/docx'),
        ),
        migrations.AddField(
            model_name='formularioproyectodeconvenio',
            name='numero_if',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='formularioproyectodisposicion',
            name='archivo_docx',
            field=models.FileField(null=True, upload_to='admisiones/formularios_disposicion/docx'),
        ),
        migrations.AddField(
            model_name='formularioproyectodisposicion',
            name='numero_if',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='informetecnico',
            name='estado_formulario',
            field=models.CharField(choices=[('borrador', 'Borrador'), ('finalizado', 'Finalizado')], default='borrador', max_length=20),
        ),
        migrations.AddField(
            model_name='informetecnicopdf',
            name='archivo_docx',
            field=models.FileField(blank=True, null=True, upload_to='admisiones/informes_tecnicos/docx'),
        ),
        migrations.AlterField(
            model_name='admision',
            name='comedor',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='admisiones_admisiones', to='comedores.comedor'),
        ),
        migrations.AlterField(
            model_name='admisionhistorial',
            name='usuario',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='admisiones_historial', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='archivoadmision',
            name='documentacion',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='admisiones.documentacion'),
        ),
        migrations.AlterField(
            model_name='archivoadmision',
            name='estado',
            field=models.CharField(choices=[('pendiente', 'Pendiente'), ('Documento adjunto', 'Documento adjunto'), ('A Validar Abogado', 'A Validar Abogado'), ('Rectificar', 'Rectificar'), ('Aceptado', 'Aceptado')], default='pendiente', max_length=20),
        ),
        migrations.AlterField(
            model_name='formularioproyectodeconvenio',
            name='admision',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='admisiones_proyecto_convenio', to='admisiones.admision'),
        ),
        migrations.AlterField(
            model_name='formularioproyectodeconvenio',
            name='archivo',
            field=models.FileField(null=True, upload_to='admisiones/formularios_convenio/pdf'),
        ),
        migrations.AlterField(
            model_name='formularioproyectodeconvenio',
            name='creado_por',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='admisiones_formularios_convenio', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='formularioproyectodisposicion',
            name='admision',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='admisiones_proyecto_disposicion', to='admisiones.admision'),
        ),
        migrations.AlterField(
            model_name='formularioproyectodisposicion',
            name='archivo',
            field=models.FileField(null=True, upload_to='admisiones/formularios_disposicion/pdf'),
        ),
        migrations.AlterField(
            model_name='formularioproyectodisposicion',
            name='creado_por',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='admisiones_formularios_disposicion', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='informecomplementario',
            name='creado_por',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='admisiones_informes_complementarios', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='informetecnico',
            name='estado',
            field=models.CharField(choices=[('Iniciado', 'Iniciado'), ('Para revision', 'Para revisión'), ('Validado', 'Validado'), ('A subsanar', 'A subsanar')], max_length=20, verbose_name='Estado del Informe'),
        ),
        migrations.RemoveField(
            model_name='informetecnico',
            name='prestaciones_almuerzo_letras',
        ),
        migrations.RemoveField(
            model_name='informetecnico',
            name='prestaciones_cena_letras',
        ),
        migrations.RemoveField(
            model_name='informetecnico',
            name='prestaciones_desayuno_letras',
        ),
        migrations.RemoveField(
            model_name='informetecnico',
            name='prestaciones_merienda_letras',
        ),
        migrations.AlterField(
            model_name='informetecnicopdf',
            name='archivo',
            field=models.FileField(upload_to='admisiones/informes_tecnicos/pdf'),
        ),
        migrations.AlterField(
            model_name='informetecnicopdf',
            name='comedor',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='admisiones_informes_tecnicos_pdf', to='comedores.comedor'),
        ),
        migrations.DeleteModel(
            name='TipoDocumentacion',
        ),
        migrations.AlterField(
            model_name='admision',
            name='comedor',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='comedores.comedor'),
        ),
        migrations.AddField(
            model_name='admision',
            name='complementario_solicitado',
            field=models.BooleanField(default=False, verbose_name='Complementario Solicitado'),
        ),
        migrations.AlterField(
            model_name='admision',
            name='estado_legales',
            field=models.CharField(blank=True, choices=[('Enviado a Legales', 'Enviado a Legales'), ('A Rectificar', 'A Rectificar'), ('Rectificado', 'Rectificado'), ('Expediente Agregado', 'Expediente Agregado'), ('Formulario Convenio Creado', 'Formulario Convenio Creado'), ('IF Convenio Asignado', 'IF Convenio Asignado'), ('Formulario Disposición Creado', 'Formulario Disposición Creado'), ('IF Disposición Asignado', 'IF Disposición Asignado'), ('Juridicos: Validado', 'Juridicos: Validado'), ('Juridicos: Rechazado', 'Juridicos: Rechazado'), ('Informe SGA Generado', 'Informe SGA Generado'), ('Convenio Firmado', 'Convenio Firmado'), ('Acompañamiento Pendiente', 'Acompañamiento Pendiente'), ('Archivado', 'Archivado'), ('Informe Complementario Solicitado', 'Informe Complementario Solicitado'), ('Informe Complementario Enviado', 'Informe Complementario Enviado'), ('Informe Complementario: Validado', 'Informe Complementario: Validado'), ('Finalizado', 'Finalizado')], max_length=40, null=True, verbose_name='Estado'),
        ),
        migrations.AddField(
            model_name='informecomplementario',
            name='estado',
            field=models.CharField(choices=[('borrador', 'Borrador'), ('enviado_validacion', 'Enviado a Validación'), ('validado', 'Validado'), ('rectificar', 'A Rectificar')], default='borrador', max_length=20),
        ),
        migrations.AddField(
            model_name='informecomplementario',
            name='modificado',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name='informecomplementario',
            name='observaciones_legales',
            field=models.TextField(blank=True, null=True, verbose_name='Observaciones de Legales'),
        ),
        migrations.CreateModel(
            name='InformeTecnicoComplementarioPDF',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tipo', models.CharField(choices=[('base', 'Base'), ('juridico', 'Jurídico')], max_length=20)),
                ('archivo', models.FileField(upload_to='admisiones/informes_complementarios_final/pdf')),
                ('archivo_docx', models.FileField(blank=True, null=True, upload_to='admisiones/informes_complementarios_final/docx')),
                ('numero_if', models.CharField(blank=True, max_length=100, null=True)),
                ('creado', models.DateTimeField(auto_now_add=True)),
                ('admision', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='admisiones.admision')),
                ('informe_complementario', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='pdf_final', to='admisiones.informecomplementario')),
            ],
        ),
        migrations.AddField(
            model_name='informetecnico',
            name='solicitudes_almuerzo_domingo',
            field=models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AddField(
            model_name='informetecnico',
            name='solicitudes_almuerzo_jueves',
            field=models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AddField(
            model_name='informetecnico',
            name='solicitudes_almuerzo_lunes',
            field=models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AddField(
            model_name='informetecnico',
            name='solicitudes_almuerzo_martes',
            field=models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AddField(
            model_name='informetecnico',
            name='solicitudes_almuerzo_miercoles',
            field=models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AddField(
            model_name='informetecnico',
            name='solicitudes_almuerzo_sabado',
            field=models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AddField(
            model_name='informetecnico',
            name='solicitudes_almuerzo_viernes',
            field=models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AddField(
            model_name='informetecnico',
            name='solicitudes_cena_domingo',
            field=models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AddField(
            model_name='informetecnico',
            name='solicitudes_cena_jueves',
            field=models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AddField(
            model_name='informetecnico',
            name='solicitudes_cena_lunes',
            field=models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AddField(
            model_name='informetecnico',
            name='solicitudes_cena_martes',
            field=models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AddField(
            model_name='informetecnico',
            name='solicitudes_cena_miercoles',
            field=models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AddField(
            model_name='informetecnico',
            name='solicitudes_cena_sabado',
            field=models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AddField(
            model_name='informetecnico',
            name='solicitudes_cena_viernes',
            field=models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AddField(
            model_name='informetecnico',
            name='solicitudes_desayuno_domingo',
            field=models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AddField(
            model_name='informetecnico',
            name='solicitudes_desayuno_jueves',
            field=models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AddField(
            model_name='informetecnico',
            name='solicitudes_desayuno_lunes',
            field=models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AddField(
            model_name='informetecnico',
            name='solicitudes_desayuno_martes',
            field=models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AddField(
            model_name='informetecnico',
            name='solicitudes_desayuno_miercoles',
            field=models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AddField(
            model_name='informetecnico',
            name='solicitudes_desayuno_sabado',
            field=models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AddField(
            model_name='informetecnico',
            name='solicitudes_desayuno_viernes',
            field=models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AddField(
            model_name='informetecnico',
            name='solicitudes_merienda_domingo',
            field=models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AddField(
            model_name='informetecnico',
            name='solicitudes_merienda_jueves',
            field=models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AddField(
            model_name='informetecnico',
            name='solicitudes_merienda_lunes',
            field=models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AddField(
            model_name='informetecnico',
            name='solicitudes_merienda_martes',
            field=models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AddField(
            model_name='informetecnico',
            name='solicitudes_merienda_miercoles',
            field=models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AddField(
            model_name='informetecnico',
            name='solicitudes_merienda_sabado',
            field=models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AddField(
            model_name='informetecnico',
            name='solicitudes_merienda_viernes',
            field=models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.RemoveField(
            model_name='informetecnico',
            name='prestaciones_almuerzo_numero',
        ),
        migrations.RemoveField(
            model_name='informetecnico',
            name='prestaciones_cena_numero',
        ),
        migrations.RemoveField(
            model_name='informetecnico',
            name='prestaciones_desayuno_numero',
        ),
        migrations.RemoveField(
            model_name='informetecnico',
            name='prestaciones_merienda_numero',
        ),
        migrations.AddField(
            model_name='informetecnico',
            name='aprobadas_almuerzo_domingo',
            field=models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AddField(
            model_name='informetecnico',
            name='aprobadas_almuerzo_jueves',
            field=models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AddField(
            model_name='informetecnico',
            name='aprobadas_almuerzo_lunes',
            field=models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AddField(
            model_name='informetecnico',
            name='aprobadas_almuerzo_martes',
            field=models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AddField(
            model_name='informetecnico',
            name='aprobadas_almuerzo_miercoles',
            field=models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AddField(
            model_name='informetecnico',
            name='aprobadas_almuerzo_sabado',
            field=models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AddField(
            model_name='informetecnico',
            name='aprobadas_almuerzo_viernes',
            field=models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AddField(
            model_name='informetecnico',
            name='aprobadas_cena_domingo',
            field=models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AddField(
            model_name='informetecnico',
            name='aprobadas_cena_jueves',
            field=models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AddField(
            model_name='informetecnico',
            name='aprobadas_cena_lunes',
            field=models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AddField(
            model_name='informetecnico',
            name='aprobadas_cena_martes',
            field=models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AddField(
            model_name='informetecnico',
            name='aprobadas_cena_miercoles',
            field=models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AddField(
            model_name='informetecnico',
            name='aprobadas_cena_sabado',
            field=models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AddField(
            model_name='informetecnico',
            name='aprobadas_cena_viernes',
            field=models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AddField(
            model_name='informetecnico',
            name='aprobadas_desayuno_domingo',
            field=models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AddField(
            model_name='informetecnico',
            name='aprobadas_desayuno_jueves',
            field=models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AddField(
            model_name='informetecnico',
            name='aprobadas_desayuno_lunes',
            field=models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AddField(
            model_name='informetecnico',
            name='aprobadas_desayuno_martes',
            field=models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AddField(
            model_name='informetecnico',
            name='aprobadas_desayuno_miercoles',
            field=models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AddField(
            model_name='informetecnico',
            name='aprobadas_desayuno_sabado',
            field=models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AddField(
            model_name='informetecnico',
            name='aprobadas_desayuno_viernes',
            field=models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AddField(
            model_name='informetecnico',
            name='aprobadas_merienda_domingo',
            field=models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AddField(
            model_name='informetecnico',
            name='aprobadas_merienda_jueves',
            field=models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AddField(
            model_name='informetecnico',
            name='aprobadas_merienda_lunes',
            field=models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AddField(
            model_name='informetecnico',
            name='aprobadas_merienda_martes',
            field=models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AddField(
            model_name='informetecnico',
            name='aprobadas_merienda_miercoles',
            field=models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AddField(
            model_name='informetecnico',
            name='aprobadas_merienda_sabado',
            field=models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AddField(
            model_name='informetecnico',
            name='aprobadas_merienda_viernes',
            field=models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AddField(
            model_name='informetecnico',
            name='plazo_ejecucion',
            field=models.CharField(blank=True, max_length=150, null=True, verbose_name='Plazo de Ejecución'),
        ),
        migrations.AddField(
            model_name='informetecnico',
            name='total_acreditaciones',
            field=models.CharField(blank=True, max_length=150, null=True, verbose_name='Total de acreditaciones a Producir'),
        ),
        migrations.AlterField(
            model_name='admision',
            name='estado_legales',
            field=models.CharField(blank=True, choices=[('Enviado a Legales', 'Enviado a Legales'), ('A Rectificar', 'A Rectificar'), ('Rectificado', 'Rectificado'), ('Pendiente de Validacion', 'Pendiente de Validacion'), ('Expediente Agregado', 'Expediente Agregado'), ('Formulario Convenio Creado', 'Formulario Convenio Creado'), ('IF Convenio Asignado', 'IF Convenio Asignado'), ('Formulario Disposición Creado', 'Formulario Disposición Creado'), ('IF Disposición Asignado', 'IF Disposición Asignado'), ('Juridicos: Validado', 'Juridicos: Validado'), ('Juridicos: Rechazado', 'Juridicos: Rechazado'), ('Informe SGA Generado', 'Informe SGA Generado'), ('Convenio Firmado', 'Convenio Firmado'), ('Acompañamiento Pendiente', 'Acompañamiento Pendiente'), ('Archivado', 'Archivado'), ('Informe Complementario Solicitado', 'Informe Complementario Solicitado'), ('Informe Complementario Enviado', 'Informe Complementario Enviado'), ('Informe Complementario: Validado', 'Informe Complementario: Validado'), ('Finalizado', 'Finalizado')], max_length=40, null=True, verbose_name='Estado'),
        ),
        migrations.AddField(
            model_name='admision',
            name='tipo',
            field=models.CharField(blank=True, choices=[('incorporacion', 'Incorporación'), ('renovacion', 'Renovación')], max_length=20, null=True, verbose_name='Tipo de Admisión'),
        ),
        migrations.AddField(
            model_name='informetecnico',
            name='monto_1',
            field=models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AddField(
            model_name='informetecnico',
            name='monto_2',
            field=models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AddField(
            model_name='informetecnico',
            name='monto_3',
            field=models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AddField(
            model_name='informetecnico',
            name='monto_4',
            field=models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AddField(
            model_name='informetecnico',
            name='monto_5',
            field=models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AddField(
            model_name='informetecnico',
            name='monto_6',
            field=models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AddField(
            model_name='informetecnico',
            name='resolucion_de_pago_1',
            field=models.CharField(blank=True, max_length=150, null=True, verbose_name='Resolución de pago 1'),
        ),
        migrations.AddField(
            model_name='informetecnico',
            name='resolucion_de_pago_2',
            field=models.CharField(blank=True, max_length=150, null=True, verbose_name='Resolución de pago 2'),
        ),
        migrations.AddField(
            model_name='informetecnico',
            name='resolucion_de_pago_3',
            field=models.CharField(blank=True, max_length=150, null=True, verbose_name='Resolución de pago 3'),
        ),
        migrations.AddField(
            model_name='informetecnico',
            name='resolucion_de_pago_4',
            field=models.CharField(blank=True, max_length=150, null=True, verbose_name='Resolución de pago 4'),
        ),
        migrations.AddField(
            model_name='informetecnico',
            name='resolucion_de_pago_5',
            field=models.CharField(blank=True, max_length=150, null=True, verbose_name='Resolución de pago 5'),
        ),
        migrations.AddField(
            model_name='informetecnico',
            name='resolucion_de_pago_6',
            field=models.CharField(blank=True, max_length=150, null=True, verbose_name='Resolución de pago 6'),
        ),
        migrations.AddField(
            model_name='informetecnico',
            name='responsable_tarjeta_cuit',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='CUIL/CUIT del Responsable de la Tarjeta'),
        ),
        migrations.AddField(
            model_name='informetecnico',
            name='domicilio_electronico_espacio',
            field=models.EmailField(blank=True, max_length=254, null=True, verbose_name='Domicilio electronico constituido del Comedor/Merendero'),
        ),
        migrations.AlterField(
            model_name='informetecnico',
            name='tipo_espacio',
            field=models.CharField(choices=[('Comedor', 'Comedor'), ('Merendero', 'Merendero'), ('Punto de Entrega', 'Punto de Entrega'), ('Comedor y Merendero', 'Comedor y Merendero')], max_length=50, verbose_name='Tipo de Espacio Comunitario'),
        ),
        migrations.AddField(
            model_name='admision',
            name='motivo_descarte_expediente',
            field=models.TextField(blank=True, null=True, verbose_name='Motivo de descarte del Expediente'),
        ),
        migrations.AddField(
            model_name='admision',
            name='fecha_descarte_expediente',
            field=models.DateField(blank=True, null=True, verbose_name='Fecha de descarte del Expediente'),
        ),
        migrations.AlterField(
            model_name='admision',
            name='estado_legales',
            field=models.CharField(blank=True, choices=[('Enviado a Legales', 'Enviado a Legales'), ('A Rectificar', 'A Rectificar'), ('Rectificado', 'Rectificado'), ('Pendiente de Validacion', 'Pendiente de Validacion'), ('Expediente Agregado', 'Expediente Agregado'), ('Formulario Convenio Creado', 'Formulario Convenio Creado'), ('IF Convenio Asignado', 'IF Convenio Asignado'), ('Formulario Disposición Creado', 'Formulario Disposición Creado'), ('IF Disposición Asignado', 'IF Disposición Asignado'), ('Juridicos: Validado', 'Juridicos: Validado'), ('Juridicos: Rechazado', 'Juridicos: Rechazado'), ('Informe SGA Generado', 'Informe SGA Generado'), ('Convenio Firmado', 'Convenio Firmado'), ('Acompañamiento Pendiente', 'Acompañamiento Pendiente'), ('Archivado', 'Archivado'), ('Informe Complementario Solicitado', 'Informe Complementario Solicitado'), ('Informe Complementario Enviado', 'Informe Complementario Enviado'), ('Informe Complementario: Validado', 'Informe Complementario: Validado'), ('Finalizado', 'Finalizado'), ('Descartado', 'Descartado')], max_length=40, null=True, verbose_name='Estado'),
        ),
        migrations.AddField(
            model_name='admision',
            name='numero_if_tecnico',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Número IF Informe Técnico'),
        ),
        migrations.AddField(
            model_name='documentacion',
            name='orden',
            field=models.PositiveIntegerField(blank=True, default=0, null=True),
        ),
        migrations.AddField(
            model_name='admision',
            name='activa',
            field=models.BooleanField(default=True, verbose_name='¿Activa?'),
        ),
        migrations.AddField(
            model_name='admision',
            name='motivo_forzar_cierre',
            field=models.TextField(blank=True, null=True, verbose_name='Motivo de forzar cierre'),
        ),
        migrations.AddField(
            model_name='admision',
            name='estado_mostrar',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='admision',
            name='fecha_estado_mostrar',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='admision',
            name='estado_admision',
            field=models.CharField(choices=[('iniciada', 'Iniciada'), ('convenio_seleccionado', 'Convenio seleccionado'), ('documentacion_en_proceso', 'Documentación en proceso'), ('documentacion_finalizada', 'Documentación finalizada'), ('documentacion_aprobada', 'Documentación aprobada'), ('expediente_cargado', 'Expediente cargado'), ('informe_tecnico_en_proceso', 'Informe técnico en proceso'), ('informe_tecnico_en_revision', 'Informe técnico en revisión'), ('informe_tecnico_en_subsanacion', 'Informe técnico en subsanación'), ('informe_tecnico_aprobado', 'Informe técnico aprobado'), ('if_informe_tecnico_cargado', 'IF Informe técnico cargado'), ('enviado_a_legales', 'Enviado a legales'), ('enviado_a_acompaniamiento', 'Enviado a acompañamiento'), ('inactivada', 'Inactivada'), ('descartado', 'Descartado')], default='iniciada', max_length=40, verbose_name='Estado de Admisión'),
        ),
        migrations.AlterField(
            model_name='admision',
            name='estado_legales',
            field=models.CharField(blank=True, choices=[('Enviado a Legales', 'Enviado a Legales'), ('A Rectificar', 'A Rectificar'), ('Rectificado', 'Rectificado'), ('Pendiente de Validacion', 'Pendiente de Validacion'), ('Expediente Agregado', 'Expediente Agregado'), ('Formulario Convenio Creado', 'Formulario Convenio Creado'), ('IF Convenio Asignado', 'IF Convenio Asignado'), ('Formulario Disposición Creado', 'Formulario Disposición Creado'), ('IF Disposición Asignado', 'IF Disposición Asignado'), ('Juridicos: Validado', 'Juridicos: Validado'), ('Juridicos: Rechazado', 'Juridicos: Rechazado'), ('Informe SGA Generado', 'Informe SGA Generado'), ('Convenio Firmado', 'Convenio Firmado'), ('Acompañamiento Pendiente', 'Acompañamiento Pendiente'), ('Archivado', 'Archivado'), ('Informe Complementario Solicitado', 'Informe Complementario Solicitado'), ('Informe Complementario Enviado', 'Informe Complementario Enviado'), ('Informe Complementario: Validado', 'Informe Complementario: Validado'), ('Finalizado', 'Finalizado'), ('Descartado', 'Descartado'), ('Inactivada', 'Inactivada')], max_length=40, null=True, verbose_name='Estado'),
        ),
        migrations.RunPython(
            code=update_estado_mostrar,
            reverse_code=reverse_update_estado_mostrar,
        ),
        migrations.AlterField(
            model_name='admision',
            name='estado_admision',
            field=models.CharField(choices=[('iniciada', 'Iniciada'), ('convenio_seleccionado', 'Convenio seleccionado'), ('documentacion_en_proceso', 'Documentación en proceso'), ('documentacion_finalizada', 'Documentación cargada'), ('documentacion_aprobada', 'Documentación aprobada'), ('expediente_cargado', 'Expediente cargado'), ('informe_tecnico_en_proceso', 'Informe técnico en proceso'), ('informe_tecnico_en_revision', 'Informe técnico en revisión'), ('informe_tecnico_en_subsanacion', 'Informe técnico en subsanación'), ('informe_tecnico_aprobado', 'Informe técnico aprobado'), ('if_informe_tecnico_cargado', 'IF Informe técnico cargado'), ('enviado_a_legales', 'Enviado a legales'), ('enviado_a_acompaniamiento', 'Enviado a acompañamiento'), ('inactivada', 'Inactivada'), ('descartado', 'Descartado')], default='iniciada', max_length=40, verbose_name='Estado de Admisión'),
        ),
        migrations.AddField(
            model_name='archivoadmision',
            name='creado_por',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='admisiones_archivos_creados', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='archivoadmision',
            name='modificado_por',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='admisiones_archivos_modificados', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='informetecnico',
            name='creado',
            field=models.DateField(auto_now_add=True, null=True),
        ),
        migrations.AddField(
            model_name='informetecnico',
            name='modificado',
            field=models.DateField(auto_now=True, null=True),
        ),
        migrations.CreateModel(
            name='HistorialEstadosAdmision',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('estado_anterior', models.CharField(blank=True, max_length=40, null=True)),
                ('estado_nuevo', models.CharField(max_length=40)),
                ('fecha', models.DateTimeField(auto_now_add=True)),
                ('admision', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='historial_estados', to='admisiones.admision')),
                ('usuario', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='admisiones_historial_estados', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AlterField(
            model_name='admision',
            name='estado_legales',
            field=models.CharField(blank=True, choices=[('Enviado a Legales', 'Enviado a Legales'), ('A Rectificar', 'A Rectificar'), ('Rectificado', 'Rectificado'), ('Pendiente de Validacion', 'Pendiente de Validacion'), ('Expediente Agregado', 'Expediente Agregado'), ('Formulario Convenio Creado', 'Formulario Convenio Creado'), ('IF Convenio Asignado', 'IF Convenio Asignado'), ('Formulario Disposición Creado', 'Formulario Disposición Creado'), ('IF Disposición Asignado', 'IF Disposición Asignado'), ('Juridicos: Validado', 'Juridicos: Validado'), ('Juridicos: Rechazado', 'Juridicos: Rechazado'), ('Disposición Firmada', 'Disposición Firmada'), ('Informe SGA Generado', 'Informe SGA Generado'), ('Convenio Firmado', 'Convenio Firmado'), ('Acompañamiento Pendiente', 'Acompañamiento Pendiente'), ('Archivado', 'Archivado'), ('Informe Complementario Solicitado', 'Informe Complementario Solicitado'), ('Informe Complementario Enviado', 'Informe Complementario Enviado'), ('Informe Complementario: Validado', 'Informe Complementario: Validado'), ('Finalizado', 'Finalizado'), ('Descartado', 'Descartado'), ('Inactivada', 'Inactivada')], max_length=40, null=True, verbose_name='Estado'),
        ),
        migrations.AddField(
            model_name='informetecnico',
            name='creado_por',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='admisiones_informes_tecnicos_creados', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='informetecnico',
            name='modificado_por',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='admisiones_informes_tecnicos_modificados', to=settings.AUTH_USER_MODEL),
        ),
        migrations.RunPython(
            code=update_documentacion_aval_labels,
            reverse_code=migrations.RunPython.noop,
        ),
        migrations.RunPython(
            code=cap_montos,
            reverse_code=migrations.RunPython.noop,
        ),
        migrations.AlterField(
            model_name='informetecnico',
            name='monto_1',
            field=models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=10, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(Decimal('99000000.00'))]),
        ),
        migrations.AlterField(
            model_name='informetecnico',
            name='monto_2',
            field=models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=10, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(Decimal('99000000.00'))]),
        ),
        migrations.AlterField(
            model_name='informetecnico',
            name='monto_3',
            field=models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=10, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(Decimal('99000000.00'))]),
        ),
        migrations.AlterField(
            model_name='informetecnico',
            name='monto_4',
            field=models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=10, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(Decimal('99000000.00'))]),
        ),
        migrations.AlterField(
            model_name='informetecnico',
            name='monto_5',
            field=models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=10, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(Decimal('99000000.00'))]),
        ),
        migrations.AlterField(
            model_name='informetecnico',
            name='monto_6',
            field=models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=10, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(Decimal('99000000.00'))]),
        ),
        migrations.AddField(
            model_name='informetecnico',
            name='no_corresponde_fecha_vencimiento',
            field=models.BooleanField(default=False, verbose_name='No corresponde fecha de vencimiento'),
        ),
        migrations.AddField(
            model_name='admision',
            name='convenio_numero',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='informetecnico',
            name='aprobadas_ultimo_convenio_desayuno_lunes',
            field=models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AddField(
            model_name='informetecnico',
            name='aprobadas_ultimo_convenio_desayuno_martes',
            field=models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AddField(
            model_name='informetecnico',
            name='aprobadas_ultimo_convenio_desayuno_miercoles',
            field=models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AddField(
            model_name='informetecnico',
            name='aprobadas_ultimo_convenio_desayuno_jueves',
            field=models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AddField(
            model_name='informetecnico',
            name='aprobadas_ultimo_convenio_desayuno_viernes',
            field=models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AddField(
            model_name='informetecnico',
            name='aprobadas_ultimo_convenio_desayuno_sabado',
            field=models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AddField(
            model_name='informetecnico',
            name='aprobadas_ultimo_convenio_desayuno_domingo',
            field=models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AddField(
            model_name='informetecnico',
            name='aprobadas_ultimo_convenio_almuerzo_lunes',
            field=models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AddField(
            model_name='informetecnico',
            name='aprobadas_ultimo_convenio_almuerzo_martes',
            field=models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AddField(
            model_name='informetecnico',
            name='aprobadas_ultimo_convenio_almuerzo_miercoles',
            field=models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AddField(
            model_name='informetecnico',
            name='aprobadas_ultimo_convenio_almuerzo_jueves',
            field=models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AddField(
            model_name='informetecnico',
            name='aprobadas_ultimo_convenio_almuerzo_viernes',
            field=models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AddField(
            model_name='informetecnico',
            name='aprobadas_ultimo_convenio_almuerzo_sabado',
            field=models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AddField(
            model_name='informetecnico',
            name='aprobadas_ultimo_convenio_almuerzo_domingo',
            field=models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AddField(
            model_name='informetecnico',
            name='aprobadas_ultimo_convenio_merienda_lunes',
            field=models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AddField(
            model_name='informetecnico',
            name='aprobadas_ultimo_convenio_merienda_martes',
            field=models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AddField(
            model_name='informetecnico',
            name='aprobadas_ultimo_convenio_merienda_miercoles',
            field=models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AddField(
            model_name='informetecnico',
            name='aprobadas_ultimo_convenio_merienda_jueves',
            field=models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AddField(
            model_name='informetecnico',
            name='aprobadas_ultimo_convenio_merienda_viernes',
            field=models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AddField(
            model_name='informetecnico',
            name='aprobadas_ultimo_convenio_merienda_sabado',
            field=models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AddField(
            model_name='informetecnico',
            name='aprobadas_ultimo_convenio_merienda_domingo',
            field=models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AddField(
            model_name='informetecnico',
            name='aprobadas_ultimo_convenio_cena_lunes',
            field=models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AddField(
            model_name='informetecnico',
            name='aprobadas_ultimo_convenio_cena_martes',
            field=models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AddField(
            model_name='informetecnico',
            name='aprobadas_ultimo_convenio_cena_miercoles',
            field=models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AddField(
            model_name='informetecnico',
            name='aprobadas_ultimo_convenio_cena_jueves',
            field=models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AddField(
            model_name='informetecnico',
            name='aprobadas_ultimo_convenio_cena_viernes',
            field=models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AddField(
            model_name='informetecnico',
            name='aprobadas_ultimo_convenio_cena_sabado',
            field=models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AddField(
            model_name='informetecnico',
            name='aprobadas_ultimo_convenio_cena_domingo',
            field=models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.RunPython(
            code=backfill_informetecnico_ultimo_convenio,
            reverse_code=migrations.RunPython.noop,
        ),
        migrations.AlterField(
            model_name='informetecnico',
            name='validacion_registro_nacional',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Validación Registro Nacional Comedores/Merenderos'),
        ),
        migrations.AlterField(
            model_name='informetecnico',
            name='estado',
            field=models.CharField(choices=[('Iniciado', 'Iniciado'), ('Para revision', 'Para revisión'), ('Docx generado', 'DOCX generado'), ('Docx editado', 'DOCX editado'), ('Validado', 'Validado'), ('A subsanar', 'A subsanar')], max_length=20, verbose_name='Estado del Informe'),
        ),
        migrations.AddField(
            model_name='informetecnico',
            name='observaciones_subsanacion',
            field=models.TextField(blank=True, help_text='Observaciones del abogado para subsanar el informe técnico', null=True, verbose_name='Observaciones de Subsanación'),
        ),
        migrations.AlterField(
            model_name='admision',
            name='estado_admision',
            field=models.CharField(choices=[('iniciada', 'Iniciada'), ('convenio_seleccionado', 'Convenio seleccionado'), ('documentacion_en_proceso', 'Documentación en proceso'), ('documentacion_finalizada', 'Documentación cargada'), ('documentacion_aprobada', 'Documentación aprobada'), ('expediente_cargado', 'Expediente cargado'), ('informe_tecnico_en_proceso', 'Informe técnico en proceso'), ('informe_tecnico_finalizado', 'Informe técnico finalizado'), ('informe_tecnico_en_revision', 'Informe técnico en revisión'), ('informe_tecnico_en_subsanacion', 'Informe técnico en subsanación'), ('informe_tecnico_aprobado', 'Informe técnico aprobado'), ('if_informe_tecnico_cargado', 'IF Informe técnico cargado'), ('enviado_a_legales', 'Enviado a legales'), ('enviado_a_acompaniamiento', 'Enviado a acompañamiento'), ('inactivada', 'Inactivada'), ('descartado', 'Descartado')], default='iniciada', max_length=40, verbose_name='Estado de Admisión'),
        ),
        migrations.AddField(
            model_name='informetecnicopdf',
            name='archivo_docx_editado',
            field=models.FileField(blank=True, help_text='DOCX editado por el técnico', null=True, upload_to='admisiones/informes_tecnicos/docx_editado'),
        ),
        migrations.AlterField(
            model_name='admision',
            name='estado_admision',
            field=models.CharField(choices=[('iniciada', 'Iniciada'), ('convenio_seleccionado', 'Convenio seleccionado'), ('documentacion_en_proceso', 'Documentación en proceso'), ('documentacion_finalizada', 'Documentación cargada'), ('documentacion_aprobada', 'Documentación aprobada'), ('expediente_cargado', 'Expediente cargado'), ('informe_tecnico_en_proceso', 'Informe técnico en proceso'), ('informe_tecnico_finalizado', 'Informe técnico finalizado'), ('informe_tecnico_docx_editado', 'Informe técnico DOCX editado'), ('informe_tecnico_en_revision', 'Informe técnico en revisión'), ('informe_tecnico_en_subsanacion', 'Informe técnico en subsanación'), ('informe_tecnico_aprobado', 'Informe técnico aprobado'), ('if_informe_tecnico_cargado', 'IF Informe técnico cargado'), ('enviado_a_legales', 'Enviado a legales'), ('enviado_a_acompaniamiento', 'Enviado a acompañamiento'), ('inactivada', 'Inactivada'), ('descartado', 'Descartado')], default='iniciada', max_length=40, verbose_name='Estado de Admisión'),
        ),
        migrations.AddField(
            model_name='admision',
            name='archivo_informe_tecnico_GDE',
            field=models.FileField(blank=True, null=True, upload_to='admisiones/informe_tecnico_GDE/'),
        ),
        migrations.AlterField(
            model_name='admision',
            name='estado_admision',
            field=models.CharField(choices=[('iniciada', 'Iniciada'), ('convenio_seleccionado', 'Convenio seleccionado'), ('documentacion_en_proceso', 'Documentación en proceso'), ('documentacion_finalizada', 'Documentación cargada'), ('documentacion_aprobada', 'Documentación aprobada'), ('expediente_cargado', 'Expediente cargado'), ('informe_tecnico_en_proceso', 'Informe técnico en proceso'), ('informe_tecnico_finalizado', 'Informe técnico finalizado'), ('informe_tecnico_docx_editado', 'Informe técnico DOCX enviado a validar'), ('informe_tecnico_en_revision', 'Informe técnico en revisión'), ('informe_tecnico_en_subsanacion', 'Informe técnico en subsanación'), ('informe_tecnico_aprobado', 'Informe técnico aprobado'), ('if_informe_tecnico_cargado', 'IF Informe técnico cargado'), ('enviado_a_legales', 'Enviado a legales'), ('enviado_a_acompaniamiento', 'Enviado a acompañamiento'), ('inactivada', 'Inactivada'), ('descartado', 'Descartado')], default='iniciada', max_length=40, verbose_name='Estado de Admisión'),
        ),
        migrations.AlterField(
            model_name='informetecnico',
            name='estado',
            field=models.CharField(choices=[('Iniciado', 'Iniciado'), ('Para revision', 'Para revisión'), ('Docx generado', 'DOCX generado'), ('Docx editado', 'DOCX enviado a validar'), ('Validado', 'Validado'), ('A subsanar', 'A subsanar')], default='Iniciado', max_length=20),
        ),
        migrations.AlterField(
            model_name='informetecnico',
            name='estado',
            field=models.CharField(choices=[('Iniciado', 'Iniciado'), ('Para revision', 'Para revisión'), ('Docx generado', 'DOCX generado'), ('Docx editado', 'DOCX enviado a validar'), ('Validado', 'Validado'), ('A subsanar', 'A subsanar')], max_length=20, verbose_name='Estado del Informe'),
        ),
        migrations.AlterModelManagers(
            name='archivoadmision',
            managers=[
                ('objects', core.soft_delete.base.SoftDeleteManager()),
                ('all_objects', core.soft_delete.base.SoftDeleteManager(include_deleted=True)),
            ],
        ),
        migrations.AddField(
            model_name='archivoadmision',
            name='deleted_at',
            field=models.DateTimeField(blank=True, db_index=True, null=True),
        ),
        migrations.AddField(
            model_name='archivoadmision',
            name='deleted_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='admision',
            name='estado_admision',
            field=models.CharField(choices=[('iniciada', 'Iniciada'), ('convenio_seleccionado', 'Convenio seleccionado'), ('documentacion_en_proceso', 'Documentación en proceso'), ('documentacion_finalizada', 'Documentación cargada'), ('documentacion_aprobada', 'Documentación aprobada'), ('documentacion_carga_finalizada', 'Carga de documentación finalizada'), ('expediente_cargado', 'Expediente cargado'), ('informe_tecnico_en_proceso', 'Informe técnico en proceso'), ('informe_tecnico_finalizado', 'Informe técnico finalizado'), ('informe_tecnico_docx_editado', 'Informe técnico DOCX enviado a validar'), ('informe_tecnico_en_revision', 'Informe técnico en revisión'), ('informe_tecnico_en_subsanacion', 'Informe técnico en subsanación'), ('informe_tecnico_aprobado', 'Informe técnico aprobado'), ('if_informe_tecnico_cargado', 'IF Informe técnico cargado'), ('enviado_a_legales', 'Enviado a legales'), ('enviado_a_acompaniamiento', 'Enviado a acompañamiento'), ('inactivada', 'Inactivada'), ('descartado', 'Descartado')], default='iniciada', max_length=40, verbose_name='Estado de Admisión'),
        ),
    ]
