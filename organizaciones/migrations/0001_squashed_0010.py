import core.soft_delete
import django.core.validators
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    replaces = [
        ("organizaciones", "0001_initial"),
        ("organizaciones", "0002_organizacion_domicilio_organizacion_localidad_and_more"),
        ("organizaciones", "0003_alter_organizacion_localidad_and_more"),
        ("organizaciones", "0004_organizacion_municipio"),
        ("organizaciones", "0005_remove_organizacion_tipo_organizacion"),
        ("organizaciones", "0006_aval_remove_aval2_organizacion_and_more"),
        ("organizaciones", "0007_organizacion_fecha_creacion"),
        ("organizaciones", "0008_alter_aval_managers_alter_firmante_managers_and_more"),
        ("organizaciones", "0009_organizacion_sigla"),
        ("organizaciones", "0010_organizacion_telefono_idx"),
    ]

    initial = True

    dependencies = [
        ("core", "0001_squashed_0007"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="RolFirmante",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nombre", models.CharField(max_length=255, unique=True)),
            ],
            options={
                "verbose_name": "Rol de Firmante",
                "verbose_name_plural": "Roles de Firmante",
                "ordering": ["id"],
            },
        ),
        migrations.CreateModel(
            name="TipoEntidad",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nombre", models.CharField(max_length=255, unique=True)),
                ("descripcion", models.CharField(blank=True, max_length=255, null=True)),
            ],
            options={
                "verbose_name": "Tipo de Entidad",
                "verbose_name_plural": "Tipos de Entidad",
                "ordering": ["nombre"],
            },
        ),
        migrations.CreateModel(
            name="TipoOrganizacion",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nombre", models.CharField(max_length=255, unique=True)),
            ],
            options={
                "verbose_name": "Tipo de Organización",
                "verbose_name_plural": "Tipos de Organización",
                "ordering": ["id"],
            },
        ),
        migrations.CreateModel(
            name="SubtipoEntidad",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nombre", models.CharField(max_length=255, unique=True)),
                (
                    "tipo_entidad",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="subtipos",
                        to="organizaciones.tipoentidad",
                    ),
                ),
            ],
            options={
                "verbose_name": "Subtipo de Entidad",
                "verbose_name_plural": "Subtipos de Entidad",
                "ordering": ["nombre"],
            },
        ),
        migrations.CreateModel(
            name="Organizacion",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nombre", models.CharField(max_length=255)),
                ("sigla", models.CharField(blank=True, max_length=30, null=True, verbose_name="Sigla")),
                (
                    "cuit",
                    models.BigIntegerField(
                        blank=True,
                        null=True,
                        unique=True,
                        validators=[
                            django.core.validators.MinValueValidator(0),
                            django.core.validators.MaxValueValidator(99999999999),
                        ],
                    ),
                ),
                ("telefono", models.BigIntegerField(blank=True, null=True)),
                ("email", models.EmailField(blank=True, max_length=254, null=True)),
                ("domicilio", models.CharField(blank=True, max_length=255, null=True)),
                (
                    "localidad",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="core.localidad",
                    ),
                ),
                ("partido", models.CharField(blank=True, max_length=255, null=True)),
                (
                    "provincia",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        to="core.provincia",
                    ),
                ),
                (
                    "municipio",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="core.municipio",
                    ),
                ),
                (
                    "tipo_entidad",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="organizaciones",
                        to="organizaciones.tipoentidad",
                    ),
                ),
                (
                    "subtipo_entidad",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="organizaciones",
                        to="organizaciones.subtipoentidad",
                    ),
                ),
                ("fecha_vencimiento", models.DateTimeField(default=django.utils.timezone.now, verbose_name="Fecha de vencimiento")),
                ("fecha_creacion", models.DateTimeField(auto_now_add=True, null=True)),
                ("deleted_at", models.DateTimeField(blank=True, db_index=True, null=True)),
                (
                    "deleted_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Organizacion",
                "verbose_name_plural": "Organizaciones",
                "ordering": ["id"],
            },
            managers=[
                ("objects", core.soft_delete.SoftDeleteManager()),
                ("all_objects", core.soft_delete.SoftDeleteManager(include_deleted=True)),
            ],
        ),
        migrations.AddIndex(
            model_name="organizacion",
            index=models.Index(fields=["telefono"], name="org_telefono_idx"),
        ),
        migrations.CreateModel(
            name="Firmante",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nombre", models.CharField(max_length=255)),
                (
                    "cuit",
                    models.BigIntegerField(
                        blank=True,
                        null=True,
                        validators=[
                            django.core.validators.MinValueValidator(0),
                            django.core.validators.MaxValueValidator(99999999999),
                        ],
                    ),
                ),
                (
                    "organizacion",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="firmantes",
                        to="organizaciones.organizacion",
                    ),
                ),
                (
                    "rol",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="firmantes",
                        to="organizaciones.rolfirmante",
                    ),
                ),
                ("deleted_at", models.DateTimeField(blank=True, db_index=True, null=True)),
                (
                    "deleted_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            managers=[
                ("objects", core.soft_delete.SoftDeleteManager()),
                ("all_objects", core.soft_delete.SoftDeleteManager(include_deleted=True)),
            ],
        ),
        migrations.CreateModel(
            name="Aval",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nombre", models.CharField(blank=True, max_length=255, null=True)),
                (
                    "cuit",
                    models.BigIntegerField(
                        blank=True,
                        null=True,
                        validators=[
                            django.core.validators.MinValueValidator(0),
                            django.core.validators.MaxValueValidator(99999999999),
                        ],
                    ),
                ),
                (
                    "organizacion",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="avales",
                        to="organizaciones.organizacion",
                    ),
                ),
                ("deleted_at", models.DateTimeField(blank=True, db_index=True, null=True)),
                (
                    "deleted_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Aval",
                "verbose_name_plural": "Avales",
            },
            managers=[
                ("objects", core.soft_delete.SoftDeleteManager()),
                ("all_objects", core.soft_delete.SoftDeleteManager(include_deleted=True)),
            ],
        ),
    ]
