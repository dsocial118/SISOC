# Generated manually for VPSL itinerary global-read permission.

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("ver_para_ser_libre", "0011_cierrediariovpsl_derivados"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="itinerariovpsl",
            options={
                "ordering": ["-fecha_inicio", "provincia__nombre"],
                "permissions": [
                    (
                        "view_all_itinerarios_vpsl",
                        "Puede ver todos los itinerarios VPSL sin restriccion provincial",
                    ),
                ],
                "verbose_name": "Itinerario VPSL",
                "verbose_name_plural": "Itinerarios VPSL",
            },
        ),
    ]
