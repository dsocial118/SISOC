from django.db import migrations, models
import django.db.models.deletion


def vincular_proyectos_existentes(apps, schema_editor):
    Rendicion = apps.get_model("rendicioncuentasmensual", "RendicionCuentaMensual")
    Proyecto = apps.get_model("organizaciones", "ProyectoOrganizacion")
    for rendicion in Rendicion.objects.filter(proyecto__isnull=True).select_related("comedor"):
        comedor = rendicion.comedor
        if not comedor:
            continue
        proyecto = getattr(comedor, "proyecto", None)
        if proyecto is None and comedor.organizacion_id and comedor.codigo_de_proyecto:
            proyecto = Proyecto.objects.filter(
                organizacion_id=comedor.organizacion_id,
                codigo=comedor.codigo_de_proyecto,
            ).first()
        if proyecto:
            rendicion.proyecto_id = proyecto.pk
            rendicion.save(update_fields=["proyecto"])


class Migration(migrations.Migration):
    dependencies = [
        ("comedores", "0055_issue_2188_personas_declaradas_siph"),
        ("organizaciones", "0020_proyecto_organizacion"),
        ("rendicioncuentasmensual", "0015_issue_2079_grupos_revision"),
    ]
    operations = [
        migrations.AddField(
            model_name="rendicioncuentamensual",
            name="proyecto",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="rendiciones_cuentas_mensuales", to="organizaciones.proyectoorganizacion"),
        ),
        migrations.RunPython(vincular_proyectos_existentes, migrations.RunPython.noop),
    ]
