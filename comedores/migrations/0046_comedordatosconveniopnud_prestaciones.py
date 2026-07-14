from django.core.validators import MinValueValidator
from django.db import migrations, models


FIELDS = [
    "aprobadas_desayuno_lunes",
    "aprobadas_desayuno_martes",
    "aprobadas_desayuno_miercoles",
    "aprobadas_desayuno_jueves",
    "aprobadas_desayuno_viernes",
    "aprobadas_desayuno_sabado",
    "aprobadas_desayuno_domingo",
    "aprobadas_almuerzo_lunes",
    "aprobadas_almuerzo_martes",
    "aprobadas_almuerzo_miercoles",
    "aprobadas_almuerzo_jueves",
    "aprobadas_almuerzo_viernes",
    "aprobadas_almuerzo_sabado",
    "aprobadas_almuerzo_domingo",
    "aprobadas_merienda_lunes",
    "aprobadas_merienda_martes",
    "aprobadas_merienda_miercoles",
    "aprobadas_merienda_jueves",
    "aprobadas_merienda_viernes",
    "aprobadas_merienda_sabado",
    "aprobadas_merienda_domingo",
    "aprobadas_cena_lunes",
    "aprobadas_cena_martes",
    "aprobadas_cena_miercoles",
    "aprobadas_cena_jueves",
    "aprobadas_cena_viernes",
    "aprobadas_cena_sabado",
    "aprobadas_cena_domingo",
]


class Migration(migrations.Migration):

    dependencies = [
        ("comedores", "0045_split_monto_convenio_por_espacio"),
    ]

    operations = [
        migrations.AddField(
            model_name="comedordatosconveniopnud",
            name=field_name,
            field=models.IntegerField(
                default=0,
                validators=[MinValueValidator(0)],
            ),
        )
        for field_name in FIELDS
    ]
