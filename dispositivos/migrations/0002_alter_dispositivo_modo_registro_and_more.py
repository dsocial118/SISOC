from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("dispositivos", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="dispositivo",
            name="modo_registro_otro",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name="dispositivo",
            name="modo_registro",
            field=models.CharField(
                blank=True,
                choices=[
                    ("sistema_propio", "Sistema digital propio"),
                    ("planillas_excel", "Planillas Excel"),
                    ("sistema_prov_mun", "Sistema provincial o municipal"),
                    ("registro_papel", "Registros en papel"),
                    ("otro", "Otro"),
                ],
                max_length=50,
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="dispositivo",
            name="tiempo_permanencia_promedio",
            field=models.CharField(
                blank=True,
                choices=[
                    ("hasta_24_hs", "Hasta 24 hs"),
                    ("1_3_dias", "1 a 3 días"),
                    ("4_7_dias", "4 a 7 días"),
                    ("1_3_meses", "1 a 3 meses"),
                    ("3_6_meses", "3 a 6 meses"),
                    ("mas_6_meses", "Más de 6 meses"),
                    ("otro", "Otro"),
                ],
                max_length=32,
                null=True,
            ),
        ),
    ]
