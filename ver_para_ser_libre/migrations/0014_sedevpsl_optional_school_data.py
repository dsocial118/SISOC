from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("ver_para_ser_libre", "0013_itinerariovpsl_create_any_province_permission"),
    ]

    operations = [
        migrations.AlterField(
            model_name="sedevpsl",
            name="sector",
            field=models.CharField(blank=True, max_length=64),
        ),
        migrations.AlterField(
            model_name="sedevpsl",
            name="ambito",
            field=models.CharField(blank=True, max_length=64),
        ),
        migrations.AlterField(
            model_name="sedevpsl",
            name="departamento",
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AlterField(
            model_name="sedevpsl",
            name="codigo_departamento",
            field=models.CharField(blank=True, max_length=32),
        ),
        migrations.AlterField(
            model_name="sedevpsl",
            name="codigo_localidad",
            field=models.CharField(blank=True, max_length=32),
        ),
        migrations.AlterField(
            model_name="sedevpsl",
            name="cueanexo",
            field=models.CharField(blank=True, max_length=32, null=True, unique=True),
        ),
    ]
