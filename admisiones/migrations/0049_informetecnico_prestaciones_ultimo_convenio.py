from django.db import migrations, models
from django.core.validators import MinValueValidator


class Migration(migrations.Migration):

    dependencies = [
        ("admisiones", "0048_admision_convenio_numero"),
    ]

    operations = [
        migrations.AddField(
            model_name="informetecnico",
            name="aprobadas_ultimo_convenio_desayuno_lunes",
            field=models.IntegerField(default=0, validators=[MinValueValidator(0)]),
        ),
        migrations.AddField(
            model_name="informetecnico",
            name="aprobadas_ultimo_convenio_desayuno_martes",
            field=models.IntegerField(default=0, validators=[MinValueValidator(0)]),
        ),
        migrations.AddField(
            model_name="informetecnico",
            name="aprobadas_ultimo_convenio_desayuno_miercoles",
            field=models.IntegerField(default=0, validators=[MinValueValidator(0)]),
        ),
        migrations.AddField(
            model_name="informetecnico",
            name="aprobadas_ultimo_convenio_desayuno_jueves",
            field=models.IntegerField(default=0, validators=[MinValueValidator(0)]),
        ),
        migrations.AddField(
            model_name="informetecnico",
            name="aprobadas_ultimo_convenio_desayuno_viernes",
            field=models.IntegerField(default=0, validators=[MinValueValidator(0)]),
        ),
        migrations.AddField(
            model_name="informetecnico",
            name="aprobadas_ultimo_convenio_desayuno_sabado",
            field=models.IntegerField(default=0, validators=[MinValueValidator(0)]),
        ),
        migrations.AddField(
            model_name="informetecnico",
            name="aprobadas_ultimo_convenio_desayuno_domingo",
            field=models.IntegerField(default=0, validators=[MinValueValidator(0)]),
        ),
        migrations.AddField(
            model_name="informetecnico",
            name="aprobadas_ultimo_convenio_almuerzo_lunes",
            field=models.IntegerField(default=0, validators=[MinValueValidator(0)]),
        ),
        migrations.AddField(
            model_name="informetecnico",
            name="aprobadas_ultimo_convenio_almuerzo_martes",
            field=models.IntegerField(default=0, validators=[MinValueValidator(0)]),
        ),
        migrations.AddField(
            model_name="informetecnico",
            name="aprobadas_ultimo_convenio_almuerzo_miercoles",
            field=models.IntegerField(default=0, validators=[MinValueValidator(0)]),
        ),
        migrations.AddField(
            model_name="informetecnico",
            name="aprobadas_ultimo_convenio_almuerzo_jueves",
            field=models.IntegerField(default=0, validators=[MinValueValidator(0)]),
        ),
        migrations.AddField(
            model_name="informetecnico",
            name="aprobadas_ultimo_convenio_almuerzo_viernes",
            field=models.IntegerField(default=0, validators=[MinValueValidator(0)]),
        ),
        migrations.AddField(
            model_name="informetecnico",
            name="aprobadas_ultimo_convenio_almuerzo_sabado",
            field=models.IntegerField(default=0, validators=[MinValueValidator(0)]),
        ),
        migrations.AddField(
            model_name="informetecnico",
            name="aprobadas_ultimo_convenio_almuerzo_domingo",
            field=models.IntegerField(default=0, validators=[MinValueValidator(0)]),
        ),
        migrations.AddField(
            model_name="informetecnico",
            name="aprobadas_ultimo_convenio_merienda_lunes",
            field=models.IntegerField(default=0, validators=[MinValueValidator(0)]),
        ),
        migrations.AddField(
            model_name="informetecnico",
            name="aprobadas_ultimo_convenio_merienda_martes",
            field=models.IntegerField(default=0, validators=[MinValueValidator(0)]),
        ),
        migrations.AddField(
            model_name="informetecnico",
            name="aprobadas_ultimo_convenio_merienda_miercoles",
            field=models.IntegerField(default=0, validators=[MinValueValidator(0)]),
        ),
        migrations.AddField(
            model_name="informetecnico",
            name="aprobadas_ultimo_convenio_merienda_jueves",
            field=models.IntegerField(default=0, validators=[MinValueValidator(0)]),
        ),
        migrations.AddField(
            model_name="informetecnico",
            name="aprobadas_ultimo_convenio_merienda_viernes",
            field=models.IntegerField(default=0, validators=[MinValueValidator(0)]),
        ),
        migrations.AddField(
            model_name="informetecnico",
            name="aprobadas_ultimo_convenio_merienda_sabado",
            field=models.IntegerField(default=0, validators=[MinValueValidator(0)]),
        ),
        migrations.AddField(
            model_name="informetecnico",
            name="aprobadas_ultimo_convenio_merienda_domingo",
            field=models.IntegerField(default=0, validators=[MinValueValidator(0)]),
        ),
        migrations.AddField(
            model_name="informetecnico",
            name="aprobadas_ultimo_convenio_cena_lunes",
            field=models.IntegerField(default=0, validators=[MinValueValidator(0)]),
        ),
        migrations.AddField(
            model_name="informetecnico",
            name="aprobadas_ultimo_convenio_cena_martes",
            field=models.IntegerField(default=0, validators=[MinValueValidator(0)]),
        ),
        migrations.AddField(
            model_name="informetecnico",
            name="aprobadas_ultimo_convenio_cena_miercoles",
            field=models.IntegerField(default=0, validators=[MinValueValidator(0)]),
        ),
        migrations.AddField(
            model_name="informetecnico",
            name="aprobadas_ultimo_convenio_cena_jueves",
            field=models.IntegerField(default=0, validators=[MinValueValidator(0)]),
        ),
        migrations.AddField(
            model_name="informetecnico",
            name="aprobadas_ultimo_convenio_cena_viernes",
            field=models.IntegerField(default=0, validators=[MinValueValidator(0)]),
        ),
        migrations.AddField(
            model_name="informetecnico",
            name="aprobadas_ultimo_convenio_cena_sabado",
            field=models.IntegerField(default=0, validators=[MinValueValidator(0)]),
        ),
        migrations.AddField(
            model_name="informetecnico",
            name="aprobadas_ultimo_convenio_cena_domingo",
            field=models.IntegerField(default=0, validators=[MinValueValidator(0)]),
        ),
    ]
