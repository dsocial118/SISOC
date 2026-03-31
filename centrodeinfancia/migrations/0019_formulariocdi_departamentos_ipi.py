from django.db import migrations, models


def _normalizar_nombre(valor):
    return " ".join((valor or "").strip().split()).casefold()


def migrar_departamentos_formulario_cdi(apps, schema_editor):
    FormularioCDI = apps.get_model("centrodeinfancia", "FormularioCDI")
    DepartamentoIpi = apps.get_model("centrodeinfancia", "DepartamentoIpi")

    departamentos_por_provincia = {}
    for departamento in DepartamentoIpi.objects.all().iterator():
        clave = (departamento.provincia_id, _normalizar_nombre(departamento.nombre))
        departamentos_por_provincia[clave] = departamento.id

    for formulario in FormularioCDI.objects.all().iterator():
        updates = []

        if formulario.provincia_cdi_id and formulario.departamento_cdi:
            clave_cdi = (
                formulario.provincia_cdi_id,
                _normalizar_nombre(formulario.departamento_cdi),
            )
            departamento_cdi_id = departamentos_por_provincia.get(clave_cdi)
            if departamento_cdi_id:
                formulario.departamento_cdi_fk_id = departamento_cdi_id
                updates.append("departamento_cdi_fk")

        if formulario.provincia_organizacion_id and formulario.departamento_organizacion:
            clave_organizacion = (
                formulario.provincia_organizacion_id,
                _normalizar_nombre(formulario.departamento_organizacion),
            )
            departamento_organizacion_id = departamentos_por_provincia.get(
                clave_organizacion
            )
            if departamento_organizacion_id:
                formulario.departamento_organizacion_fk_id = (
                    departamento_organizacion_id
                )
                updates.append("departamento_organizacion_fk")

        if updates:
            formulario.save(update_fields=updates)


def revertir_departamentos_formulario_cdi(apps, schema_editor):
    FormularioCDI = apps.get_model("centrodeinfancia", "FormularioCDI")

    for formulario in FormularioCDI.objects.select_related(
        "departamento_cdi_fk",
        "departamento_organizacion_fk",
    ).iterator():
        updates = []

        if formulario.departamento_cdi_fk_id:
            formulario.departamento_cdi = formulario.departamento_cdi_fk.nombre
            updates.append("departamento_cdi")

        if formulario.departamento_organizacion_fk_id:
            formulario.departamento_organizacion = (
                formulario.departamento_organizacion_fk.nombre
            )
            updates.append("departamento_organizacion")

        if updates:
            formulario.save(update_fields=updates)


class Migration(migrations.Migration):
    dependencies = [
        (
            "centrodeinfancia",
            "0018_alter_formulariocdiwaitlistbyagegroup_grupo_etario",
        ),
    ]

    operations = [
        migrations.AddField(
            model_name="formulariocdi",
            name="departamento_cdi_fk",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=models.deletion.SET_NULL,
                related_name="+",
                to="centrodeinfancia.departamentoipi",
            ),
        ),
        migrations.AddField(
            model_name="formulariocdi",
            name="departamento_organizacion_fk",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=models.deletion.SET_NULL,
                related_name="+",
                to="centrodeinfancia.departamentoipi",
            ),
        ),
        migrations.RunPython(
            migrar_departamentos_formulario_cdi,
            reverse_code=revertir_departamentos_formulario_cdi,
        ),
        migrations.RemoveField(
            model_name="formulariocdi",
            name="departamento_cdi",
        ),
        migrations.RemoveField(
            model_name="formulariocdi",
            name="departamento_organizacion",
        ),
        migrations.RenameField(
            model_name="formulariocdi",
            old_name="departamento_cdi_fk",
            new_name="departamento_cdi",
        ),
        migrations.RenameField(
            model_name="formulariocdi",
            old_name="departamento_organizacion_fk",
            new_name="departamento_organizacion",
        ),
    ]
