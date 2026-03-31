from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0008_programa_organismo_programa_descripcion"),
        ("centrodeinfancia", "0020_alter_formulariocdi_cobertura_educadora_titulo_habilitante_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="nominacentroinfancia",
            name="adulto_responsable_apellido",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="nominacentroinfancia",
            name="adulto_responsable_dni",
            field=models.PositiveBigIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="nominacentroinfancia",
            name="adulto_responsable_nombre",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="nominacentroinfancia",
            name="adulto_responsable_parentesco",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="nominacentroinfancia",
            name="adulto_responsable_telefono",
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name="nominacentroinfancia",
            name="apellido",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="nominacentroinfancia",
            name="calendario_vacunacion_al_dia",
            field=models.BooleanField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="nominacentroinfancia",
            name="calle_domicilio",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="nominacentroinfancia",
            name="departamento_domicilio",
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name="nominacentroinfancia",
            name="discapacidad_tipo",
            field=models.CharField(
                blank=True,
                choices=[
                    ("motora", "Motora"),
                    ("visual", "Visual"),
                    ("auditiva", "Auditiva"),
                    ("intelectual", "Intelectual"),
                    ("mental", "Mental"),
                    ("visceral", "Visceral"),
                    ("multiple", "Múltiple"),
                    ("ns_nc", "Ns/Nc"),
                ],
                max_length=32,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="nominacentroinfancia",
            name="dni",
            field=models.PositiveBigIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="nominacentroinfancia",
            name="fecha_nacimiento",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="nominacentroinfancia",
            name="habla_lengua_originaria_hogar",
            field=models.CharField(
                blank=True,
                choices=[("si", "Si"), ("no", "No"), ("ns_nc", "Ns/Nc")],
                max_length=16,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="nominacentroinfancia",
            name="altura_domicilio",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="nominacentroinfancia",
            name="localidad_domicilio",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="+",
                to="core.localidad",
            ),
        ),
        migrations.AddField(
            model_name="nominacentroinfancia",
            name="municipio_domicilio",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="+",
                to="core.municipio",
            ),
        ),
        migrations.AddField(
            model_name="nominacentroinfancia",
            name="nacionalidad",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="nominacentroinfancia",
            name="nombre",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="nominacentroinfancia",
            name="pertenece_pueblo_originario",
            field=models.CharField(
                blank=True,
                choices=[("si", "Si"), ("no", "No"), ("ns_nc", "Ns/Nc")],
                max_length=16,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="nominacentroinfancia",
            name="peso",
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                max_digits=6,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="nominacentroinfancia",
            name="piso_domicilio",
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name="nominacentroinfancia",
            name="posee_cud",
            field=models.BooleanField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="nominacentroinfancia",
            name="posee_obra_social",
            field=models.BooleanField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="nominacentroinfancia",
            name="provincia_domicilio",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="+",
                to="core.provincia",
            ),
        ),
        migrations.AddField(
            model_name="nominacentroinfancia",
            name="pueblo_originario_cual",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="nominacentroinfancia",
            name="recibe_apoyo_discapacidad",
            field=models.BooleanField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="nominacentroinfancia",
            name="responsable_legal_1_apellido",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="nominacentroinfancia",
            name="responsable_legal_1_dni",
            field=models.PositiveBigIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="nominacentroinfancia",
            name="responsable_legal_1_nombre",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="nominacentroinfancia",
            name="responsable_legal_1_percibe_alimenta",
            field=models.CharField(
                blank=True,
                choices=[("si", "Si"), ("no", "No"), ("ns_nc", "Ns/Nc")],
                max_length=16,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="nominacentroinfancia",
            name="responsable_legal_1_percibe_auh",
            field=models.CharField(
                blank=True,
                choices=[("si", "Si"), ("no", "No"), ("ns_nc", "Ns/Nc")],
                max_length=16,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="nominacentroinfancia",
            name="responsable_legal_1_telefono",
            field=models.PositiveBigIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="nominacentroinfancia",
            name="responsable_legal_2_apellido",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="nominacentroinfancia",
            name="responsable_legal_2_dni",
            field=models.PositiveBigIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="nominacentroinfancia",
            name="responsable_legal_2_nombre",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="nominacentroinfancia",
            name="responsable_legal_2_percibe_alimenta",
            field=models.CharField(
                blank=True,
                choices=[("si", "Si"), ("no", "No"), ("ns_nc", "Ns/Nc")],
                max_length=16,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="nominacentroinfancia",
            name="responsable_legal_2_percibe_auh",
            field=models.CharField(
                blank=True,
                choices=[("si", "Si"), ("no", "No"), ("ns_nc", "Ns/Nc")],
                max_length=16,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="nominacentroinfancia",
            name="responsable_legal_2_telefono",
            field=models.PositiveBigIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="nominacentroinfancia",
            name="sala",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="nominacentroinfancia",
            name="sexo",
            field=models.CharField(
                blank=True,
                choices=[
                    ("Femenino", "Femenino"),
                    ("Masculino", "Masculino"),
                    ("X", "X"),
                ],
                max_length=20,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="nominacentroinfancia",
            name="talla",
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name="nominacentroinfancia",
            name="tiene_discapacidad",
            field=models.CharField(
                blank=True,
                choices=[("si", "Si"), ("no", "No"), ("ns_nc", "Ns/Nc")],
                max_length=16,
                null=True,
            ),
        ),
    ]
