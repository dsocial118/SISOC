from django.db import migrations, models
import django.db.models.deletion


def migrar_proyectos(apps, schema_editor):
    Comedor = apps.get_model("comedores", "Comedor")
    Proyecto = apps.get_model("organizaciones", "ProyectoOrganizacion")

    comedores = Comedor.objects.exclude(organizacion_id=None).exclude(
        codigo_de_proyecto__isnull=True
    )
    for comedor in comedores.iterator():
        codigo = (comedor.codigo_de_proyecto or "").strip()
        if not codigo:
            continue
        proyecto, _ = Proyecto.objects.get_or_create(
            organizacion_id=comedor.organizacion_id,
            codigo=codigo,
        )
        comedor.proyecto_id = proyecto.pk
        comedor.codigo_de_proyecto = codigo
        comedor.save(update_fields=["proyecto", "codigo_de_proyecto"])


class Migration(migrations.Migration):
    dependencies = [
        ("organizaciones", "0020_proyecto_organizacion"),
        ("comedores", "0052_issue_2169_codigo_proyecto"),
    ]

    operations = [
        migrations.AddField(
            model_name="comedor",
            name="proyecto",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="comedores",
                to="organizaciones.proyectoorganizacion",
            ),
        ),
        migrations.RunPython(migrar_proyectos, migrations.RunPython.noop),
    ]
