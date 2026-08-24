from django.db import migrations


def crear_grupos_revision(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")
    permisos = Permission.objects.filter(
        content_type__app_label="rendicioncuentasmensual",
        content_type__model="rendicioncuentamensual",
        codename__in=[
            "view_rendicioncuentamensual",
            "change_rendicioncuentamensual",
        ],
    )
    for nombre in [
        "Rendición Territorial",
        "Rendición Auditoría",
        "Administrador Auditoría",
    ]:
        grupo, _ = Group.objects.get_or_create(name=nombre)
        grupo.permissions.add(*permisos)


def migrar_estados_existentes(apps, schema_editor):
    Rendicion = apps.get_model("rendicioncuentasmensual", "RendicionCuentaMensual")
    Rendicion.objects.filter(estado="revision").update(
        etapa_proceso="revision_documentacion",
        subestado_proceso="en_curso",
    )
    Rendicion.objects.filter(estado="subsanar").update(
        etapa_proceso="revision_documentacion",
        subestado_proceso="pendiente_correcciones",
    )
    finalizadas = Rendicion.objects.filter(estado="finalizada")
    for rendicion in finalizadas.iterator():
        rendicion.etapa_proceso = "revision_auditoria"
        rendicion.subestado_proceso = "pendiente"
        rendicion.fecha_validacion_territorial = rendicion.ultima_modificacion
        rendicion.save(
            update_fields=[
                "etapa_proceso",
                "subestado_proceso",
                "fecha_validacion_territorial",
            ]
        )


class Migration(migrations.Migration):
    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
        ("rendicioncuentasmensual", "0014_issue_2005_datos_auditoria"),
    ]

    operations = [
        migrations.RunPython(migrar_estados_existentes, migrations.RunPython.noop),
        migrations.RunPython(crear_grupos_revision, migrations.RunPython.noop),
    ]
