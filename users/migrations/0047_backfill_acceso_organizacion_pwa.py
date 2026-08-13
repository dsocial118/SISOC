from django.db import migrations


def backfill_memberships(apps, schema_editor):
    """Deriva la membresía usuario-organización de los accesos PWA vigentes."""
    AccesoComedorPWA = apps.get_model("users", "AccesoComedorPWA")
    AccesoOrganizacionPWA = apps.get_model("users", "AccesoOrganizacionPWA")

    pares = (
        AccesoComedorPWA.objects.filter(
            rol="representante",
            tipo_asociacion="organizacion",
            activo=True,
            organizacion__isnull=False,
        )
        .values_list("user_id", "organizacion_id")
        .distinct()
    )
    existentes = set(
        AccesoOrganizacionPWA.objects.values_list("user_id", "organizacion_id")
    )
    nuevos = [
        AccesoOrganizacionPWA(user_id=user_id, organizacion_id=organizacion_id)
        for user_id, organizacion_id in pares
        if (user_id, organizacion_id) not in existentes
    ]
    AccesoOrganizacionPWA.objects.bulk_create(nuevos, batch_size=500)


def borrar_memberships(apps, schema_editor):
    apps.get_model("users", "AccesoOrganizacionPWA").objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0046_acceso_organizacion_pwa"),
    ]

    operations = [
        migrations.RunPython(backfill_memberships, borrar_memberships),
    ]
