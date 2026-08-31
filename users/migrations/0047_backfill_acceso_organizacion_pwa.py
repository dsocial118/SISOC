from django.db import migrations


def backfill_memberships(apps, schema_editor):
    """Deriva la membresía usuario-organización de los accesos PWA vigentes."""
    AccesoComedorPWA = apps.get_model("users", "AccesoComedorPWA")
    AccesoOrganizacionPWA = apps.get_model("users", "AccesoOrganizacionPWA")
    database_alias = schema_editor.connection.alias

    pares = (
        AccesoComedorPWA.objects.using(database_alias)
        .filter(
            rol="representante",
            tipo_asociacion="organizacion",
            activo=True,
            organizacion__isnull=False,
        )
        .values_list("user_id", "organizacion_id")
        .distinct()
    )
    nuevos = []
    for user_id, organizacion_id in pares.iterator(chunk_size=2000):
        nuevos.append(
            AccesoOrganizacionPWA(
                user_id=user_id,
                organizacion_id=organizacion_id,
            )
        )
        if len(nuevos) == 500:
            AccesoOrganizacionPWA.objects.using(database_alias).bulk_create(
                nuevos,
                ignore_conflicts=True,
            )
            nuevos.clear()
    if nuevos:
        AccesoOrganizacionPWA.objects.using(database_alias).bulk_create(
            nuevos,
            ignore_conflicts=True,
        )


def borrar_memberships(apps, schema_editor):
    apps.get_model("users", "AccesoOrganizacionPWA").objects.using(
        schema_editor.connection.alias
    ).all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0046_acceso_organizacion_pwa"),
    ]

    operations = [
        migrations.RunPython(backfill_memberships, borrar_memberships),
    ]
