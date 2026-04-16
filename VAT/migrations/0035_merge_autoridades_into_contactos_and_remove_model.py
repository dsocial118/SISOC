from django.db import migrations


def merge_autoridades_into_contactos(apps, schema_editor):
    AutoridadInstitucional = apps.get_model("VAT", "AutoridadInstitucional")
    InstitucionContacto = apps.get_model("VAT", "InstitucionContacto")

    for autoridad in AutoridadInstitucional.objects.all().order_by(
        "centro_id", "-es_actual", "id"
    ):
        if autoridad.email:
            tipo = "email"
            valor = autoridad.email
        else:
            tipo = "telefono"
            valor = autoridad.telefono or autoridad.dni or f"autoridad-{autoridad.pk}"

        contacto, created = InstitucionContacto.objects.get_or_create(
            centro_id=autoridad.centro_id,
            tipo=tipo,
            valor=valor,
            defaults={
                "nombre_contacto": autoridad.nombre_completo,
                "rol_area": autoridad.cargo,
                "documento": autoridad.dni,
                "telefono_contacto": autoridad.telefono,
                "email_contacto": autoridad.email,
                "es_principal": autoridad.es_actual,
                "vigencia_desde": autoridad.vigencia_desde,
                "vigencia_hasta": autoridad.vigencia_hasta,
            },
        )
        if created and autoridad.vigencia_desde:
            contacto.vigencia_desde = autoridad.vigencia_desde
            contacto.save(update_fields=["vigencia_desde"])
        if created:
            continue

        updated_fields = []
        merged_fields = {
            "nombre_contacto": autoridad.nombre_completo,
            "rol_area": autoridad.cargo,
            "documento": autoridad.dni,
            "telefono_contacto": autoridad.telefono,
            "email_contacto": autoridad.email,
            "vigencia_hasta": autoridad.vigencia_hasta,
        }
        for field_name, value in merged_fields.items():
            if value and not getattr(contacto, field_name):
                setattr(contacto, field_name, value)
                updated_fields.append(field_name)
        if (
            autoridad.vigencia_desde
            and contacto.vigencia_desde
            and autoridad.vigencia_desde < contacto.vigencia_desde
        ):
            contacto.vigencia_desde = autoridad.vigencia_desde
            updated_fields.append("vigencia_desde")
        if autoridad.es_actual and not contacto.es_principal:
            contacto.es_principal = True
            updated_fields.append("es_principal")
        if updated_fields:
            contacto.save(update_fields=updated_fields)


class Migration(migrations.Migration):

    dependencies = [
        ("VAT", "0034_institucioncontacto_documento"),
    ]

    operations = [
        migrations.RunPython(
            merge_autoridades_into_contactos,
            reverse_code=migrations.RunPython.noop,
        ),
        migrations.DeleteModel(name="AutoridadInstitucional"),
    ]
