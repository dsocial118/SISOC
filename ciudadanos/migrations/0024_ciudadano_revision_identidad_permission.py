from django.db import migrations


class Migration(migrations.Migration):
    """
    Crea el permiso custom 'revision_identidad' en ciudadanos.Ciudadano.
    Se asigna manualmente desde el admin de Django a usuarios o grupos
    que deban gestionar la cola de revisión de identidad.
    """

    dependencies = [
        ("ciudadanos", "0023_ciudadano_identidad_fase1"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="ciudadano",
            options={
                "ordering": ["apellido", "nombre"],
                "permissions": [
                    (
                        "revision_identidad",
                        "Puede revisar y cerrar casos de identidad pendientes",
                    )
                ],
            },
        ),
    ]
