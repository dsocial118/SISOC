from django.db import migrations, models
import django.db.models.deletion
import django.contrib.postgres.indexes


class Migration(migrations.Migration):

    dependencies = [
        ("VAT", "0008_centro_der_v4_fields"),
    ]

    operations = [
        migrations.CreateModel(
            name="Sector",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "deleted_at",
                    models.DateTimeField(blank=True, editable=False, null=True),
                ),
                (
                    "nombre",
                    models.CharField(
                        max_length=100, verbose_name="Nombre del sector"
                    ),
                ),
                (
                    "descripcion",
                    models.TextField(
                        blank=True, null=True, verbose_name="Descripción"
                    ),
                ),
            ],
            options={
                "verbose_name": "Sector",
                "verbose_name_plural": "Sectores",
                "ordering": ["nombre"],
            },
        ),
        migrations.CreateModel(
            name="Subsector",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "deleted_at",
                    models.DateTimeField(blank=True, editable=False, null=True),
                ),
                (
                    "nombre",
                    models.CharField(
                        max_length=100, verbose_name="Nombre del subsector"
                    ),
                ),
                (
                    "descripcion",
                    models.TextField(
                        blank=True, null=True, verbose_name="Descripción"
                    ),
                ),
                (
                    "sector",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="subsectores",
                        to="VAT.sector",
                        verbose_name="Sector",
                    ),
                ),
            ],
            options={
                "verbose_name": "Subsector",
                "verbose_name_plural": "Subsectores",
                "ordering": ["sector", "nombre"],
                "unique_together": {("sector", "nombre")},
            },
        ),
        migrations.CreateModel(
            name="ModalidadCursada",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "nombre",
                    models.CharField(
                        max_length=100, verbose_name="Nombre de la modalidad"
                    ),
                ),
                (
                    "descripcion",
                    models.TextField(
                        blank=True, null=True, verbose_name="Descripción"
                    ),
                ),
                (
                    "activo",
                    models.BooleanField(default=True, verbose_name="Activo"),
                ),
            ],
            options={
                "verbose_name": "Modalidad de Cursado",
                "verbose_name_plural": "Modalidades de Cursado",
                "ordering": ["nombre"],
            },
        ),
        migrations.CreateModel(
            name="TituloReferencia",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "deleted_at",
                    models.DateTimeField(blank=True, editable=False, null=True),
                ),
                (
                    "codigo_referencia",
                    models.CharField(
                        blank=True,
                        max_length=50,
                        null=True,
                        verbose_name="Código de Referencia",
                    ),
                ),
                (
                    "nombre",
                    models.CharField(
                        max_length=200, verbose_name="Nombre del título"
                    ),
                ),
                (
                    "descripcion",
                    models.TextField(
                        blank=True, null=True, verbose_name="Descripción"
                    ),
                ),
                (
                    "activo",
                    models.BooleanField(default=True, verbose_name="Activo"),
                ),
                (
                    "sector",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="titulos",
                        to="VAT.sector",
                        verbose_name="Sector",
                    ),
                ),
                (
                    "subsector",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="titulos",
                        to="VAT.subsector",
                        verbose_name="Subsector",
                    ),
                ),
            ],
            options={
                "verbose_name": "Título de Referencia",
                "verbose_name_plural": "Títulos de Referencia",
                "ordering": ["nombre"],
            },
        ),
        migrations.CreateModel(
            name="PlanVersionCurricular",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "deleted_at",
                    models.DateTimeField(blank=True, editable=False, null=True),
                ),
                (
                    "normativa",
                    models.CharField(
                        blank=True,
                        max_length=200,
                        null=True,
                        verbose_name="Normativa",
                    ),
                ),
                (
                    "version",
                    models.CharField(
                        blank=True,
                        max_length=50,
                        null=True,
                        verbose_name="Versión",
                    ),
                ),
                (
                    "horas_reloj",
                    models.PositiveIntegerField(
                        blank=True, null=True, verbose_name="Horas Reloj"
                    ),
                ),
                (
                    "nivel_requerido",
                    models.CharField(
                        blank=True,
                        max_length=100,
                        null=True,
                        verbose_name="Nivel Requerido",
                    ),
                ),
                (
                    "nivel_certifica",
                    models.CharField(
                        blank=True,
                        max_length=100,
                        null=True,
                        verbose_name="Nivel que Certifica",
                    ),
                ),
                (
                    "frecuencia",
                    models.CharField(
                        blank=True,
                        max_length=100,
                        null=True,
                        verbose_name="Frecuencia",
                    ),
                ),
                (
                    "activo",
                    models.BooleanField(default=True, verbose_name="Activo"),
                ),
                (
                    "modalidad_cursada",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="planes",
                        to="VAT.modalidadcursada",
                        verbose_name="Modalidad de Cursado",
                    ),
                ),
                (
                    "titulo_referencia",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="planes",
                        to="VAT.tituloreferencia",
                        verbose_name="Título de Referencia",
                    ),
                ),
            ],
            options={
                "verbose_name": "Plan / Versión Curricular",
                "verbose_name_plural": "Planes / Versiones Curriculares",
                "ordering": ["titulo_referencia", "modalidad_cursada"],
                "unique_together": {
                    ("titulo_referencia", "modalidad_cursada", "version")
                },
            },
        ),
        migrations.AddIndex(
            model_name="subsector",
            index=django.contrib.postgres.indexes.GinIndex(
                fields=["nombre"],
                name="vat_subsector_nombre_trgm",
                opclasses=["gin_trgm_ops"],
            ),
        ),
        migrations.AddIndex(
            model_name="titulor eferencia",
            index=django.contrib.postgres.indexes.GinIndex(
                fields=["nombre"],
                name="vat_titloreferencia_nombre_trgm",
                opclasses=["gin_trgm_ops"],
            ),
        ),
        migrations.AddIndex(
            model_name="sector",
            index=django.contrib.postgres.indexes.GinIndex(
                fields=["nombre"],
                name="vat_sector_nombre_trgm",
                opclasses=["gin_trgm_ops"],
            ),
        ),
    ]
