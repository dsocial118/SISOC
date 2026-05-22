from django.conf import settings
from django.db import migrations, models


def forwards_backfill(apps, schema_editor):
    """Si una organizacion tiene ``ArchivoOrganizacion.numero_gde`` cargado y
    existe una unica admision asociada al comedor de esa organizacion, copiamos
    el valor para no perderlo. Si hay mas de una admision, no copiamos para
    evitar ambiguedad (cada admision pasara a manejar su propio GDE)."""

    ArchivoOrganizacion = apps.get_model("organizaciones", "ArchivoOrganizacion")
    Admision = apps.get_model("admisiones", "Admision")
    NumeroGdeOrganizacion = apps.get_model("admisiones", "NumeroGdeOrganizacion")

    archivos = ArchivoOrganizacion.objects.exclude(numero_gde__isnull=True).exclude(
        numero_gde=""
    )
    for archivo in archivos.iterator(chunk_size=500):
        admisiones_ids = list(
            Admision.objects.filter(
                comedor__organizacion_id=archivo.organizacion_id
            ).values_list("id", flat=True)
        )
        if len(admisiones_ids) != 1:
            continue
        NumeroGdeOrganizacion.objects.update_or_create(
            admision_id=admisiones_ids[0],
            archivo_organizacion_id=archivo.id,
            defaults={"numero_gde": archivo.numero_gde},
        )


class Migration(migrations.Migration):
    dependencies = [
        ("admisiones", "0059_admision_tipo_entidad_origen"),
        ("organizaciones", "0013_archivoorganizacion_numero_gde"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="NumeroGdeOrganizacion",
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
                    "numero_gde",
                    models.CharField(
                        blank=True,
                        help_text=(
                            "Numero de expediente GDE asignado por la"
                            " admision al documento de la organizacion."
                        ),
                        max_length=50,
                        null=True,
                        verbose_name="Numero de GDE",
                    ),
                ),
                ("creado", models.DateTimeField(auto_now_add=True)),
                ("modificado", models.DateTimeField(auto_now=True)),
                (
                    "admision",
                    models.ForeignKey(
                        on_delete=models.deletion.CASCADE,
                        related_name="numeros_gde_organizacion",
                        to="admisiones.admision",
                    ),
                ),
                (
                    "archivo_organizacion",
                    models.ForeignKey(
                        on_delete=models.deletion.CASCADE,
                        related_name="numeros_gde_por_admision",
                        to="organizaciones.archivoorganizacion",
                    ),
                ),
                (
                    "modificado_por",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=models.deletion.SET_NULL,
                        related_name="numeros_gde_organizacion_modificados",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": (
                    "Numero GDE de archivo de organizacion por admision"
                ),
                "verbose_name_plural": (
                    "Numeros GDE de archivos de organizacion por admision"
                ),
            },
        ),
        migrations.AddConstraint(
            model_name="numerogdeorganizacion",
            constraint=models.UniqueConstraint(
                fields=("admision", "archivo_organizacion"),
                name="unq_gde_admision_archivoorg",
            ),
        ),
        migrations.RunPython(forwards_backfill, migrations.RunPython.noop),
    ]
