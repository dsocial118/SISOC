from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("ver_para_ser_libre", "0012_itinerariovpsl_view_all_permission"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="itinerariovpsl",
            options={
                "ordering": ["-fecha_inicio", "provincia__nombre"],
                "permissions": [
                    (
                        "create_itinerarios_any_province_vpsl",
                        "Puede crear itinerarios VPSL en cualquier provincia",
                    ),
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
