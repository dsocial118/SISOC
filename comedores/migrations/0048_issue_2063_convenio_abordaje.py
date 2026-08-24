from django.core.validators import MinValueValidator
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("comedores", "0047_remove_conformidad_periodo_unique")]

    operations = [
        *[
            migrations.AddField(
                model_name="comedordatosconveniopnud",
                name=f"prestaciones_financiadas_diarias_{comida}",
                field=models.PositiveIntegerField(blank=True, null=True),
            )
            for comida in (
                "desayuno",
                "almuerzo",
                "merienda",
                "merienda_reforzada",
                "cena",
            )
        ],
        *[
            migrations.AddField(
                model_name="comedordatosconveniopnud",
                name=f"aprobadas_merienda_reforzada_{dia}",
                field=models.IntegerField(default=0, validators=[MinValueValidator(0)]),
            )
            for dia in (
                "lunes",
                "martes",
                "miercoles",
                "jueves",
                "viernes",
                "sabado",
                "domingo",
            )
        ],
    ]
