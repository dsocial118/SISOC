# Generated by Django 4.0.2 on 2024-09-11 17:37

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("legajos", "0001_initial"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="legajolocalidad",
            options={"verbose_name": "Localidad", "verbose_name_plural": "Localidad"},
        ),
        migrations.AlterModelOptions(
            name="legajomunicipio",
            options={
                "ordering": ["id"],
                "verbose_name": "Municipio",
                "verbose_name_plural": "Municipio",
            },
        ),
        migrations.AlterModelOptions(
            name="legajoprovincias",
            options={
                "ordering": ["id"],
                "verbose_name": "Provincia",
                "verbose_name_plural": "Provincia",
            },
        ),
        migrations.RemoveIndex(
            model_name="legajomunicipio",
            name="legajos_leg_id_631aa8_idx",
        ),
        migrations.RemoveIndex(
            model_name="legajoprovincias",
            name="legajos_leg_id_62b98d_idx",
        ),
        migrations.AlterField(
            model_name="dimensioneducacion",
            name="localidadInstitucion",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="legajos.legajolocalidad",
            ),
        ),
        migrations.AlterField(
            model_name="dimensioneducacion",
            name="municipioInstitucion",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="legajos.legajomunicipio",
            ),
        ),
        migrations.AlterField(
            model_name="dimensioneducacion",
            name="provinciaInstitucion",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="legajos.legajoprovincias",
            ),
        ),
        migrations.AlterField(
            model_name="legajos",
            name="fk_localidad",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="legajos.legajolocalidad",
            ),
        ),
        migrations.AlterField(
            model_name="legajos",
            name="fk_municipio",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="legajos.legajomunicipio",
            ),
        ),
        migrations.AlterField(
            model_name="legajos",
            name="fk_provincia",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="legajos.legajoprovincias",
            ),
        ),
        migrations.AddIndex(
            model_name="legajolocalidad",
            index=models.Index(
                fields=["departamento_id"], name="legajos_leg_departa_4025ff_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="legajomunicipio",
            index=models.Index(
                fields=["codigo_ifam"], name="legajos_leg_codigo__94af32_idx"
            ),
        ),
    ]
