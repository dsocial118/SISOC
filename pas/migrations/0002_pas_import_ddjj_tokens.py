import django.db.models.deletion
import pas.models
import uuid
from django.conf import settings
from django.db import migrations, models
from django.db.models import Q
from django.utils import timezone


def crear_tokens_faltantes(apps, schema_editor):
    persona_model = apps.get_model("pas", "PasPersona")
    invitacion_model = apps.get_model("pas", "PasInvitacionDDJJ")
    personas_con_token = (
        invitacion_model.objects.filter(
            utilizada__isnull=True,
            revocada__isnull=True,
        )
        .filter(Q(vence__isnull=True) | Q(vence__gt=timezone.now()))
        .values_list("persona_id", flat=True)
    )
    personas_sin_token = (
        persona_model.objects.exclude(pk__in=personas_con_token)
        .order_by("pk")
        .values_list("pk", flat=True)
        .iterator(chunk_size=1000)
    )
    lote = []
    for persona_id in personas_sin_token:
        lote.append(invitacion_model(persona_id=persona_id, token=uuid.uuid4()))
        if len(lote) == 1000:
            invitacion_model.objects.bulk_create(lote, batch_size=1000)
            lote = []
    invitacion_model.objects.bulk_create(lote, batch_size=1000)


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("pas", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="paspersona",
            name="correo_electronico",
            field=models.EmailField(blank=True, max_length=254),
        ),
        migrations.AddField(
            model_name="paspersona",
            name="domicilio",
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name="paspersona",
            name="telefono_celular",
            field=models.CharField(blank=True, max_length=30),
        ),
        migrations.CreateModel(
            name="PasInvitacionDDJJ",
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
                    "token",
                    models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
                ),
                ("creada", models.DateTimeField(auto_now_add=True)),
                ("vence", models.DateTimeField(blank=True, null=True)),
                ("utilizada", models.DateTimeField(blank=True, null=True)),
                ("revocada", models.DateTimeField(blank=True, null=True)),
                (
                    "creada_por",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="invitaciones_ddjj_pas",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "persona",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="invitaciones_ddjj",
                        to="pas.paspersona",
                    ),
                ),
            ],
            options={
                "verbose_name": "Invitación a DDJJ PAS",
                "verbose_name_plural": "Invitaciones a DDJJ PAS",
                "ordering": ["-creada", "-id"],
            },
        ),
        migrations.CreateModel(
            name="PasDeclaracionJurada",
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
                ("version", models.PositiveIntegerField()),
                ("presentada", models.DateTimeField(auto_now_add=True)),
                ("domicilio", models.CharField(max_length=255)),
                ("correo_electronico", models.EmailField(max_length=254)),
                ("telefono_celular", models.CharField(max_length=30)),
                ("datos_mi_argentina_confirmados", models.BooleanField()),
                ("embarazada", models.BooleanField()),
                (
                    "controles_embarazo_cumplidos",
                    models.BooleanField(blank=True, null=True),
                ),
                ("hijos_menores_a_cargo", models.BooleanField()),
                ("vacunacion_cumplida", models.BooleanField(blank=True, null=True)),
                (
                    "regularidad_escolar_acreditada",
                    models.BooleanField(blank=True, null=True),
                ),
                ("gastos_bajo_limite_smvm", models.BooleanField()),
                ("no_accedio_mercado_cambios", models.BooleanField()),
                ("acepto_declaracion", models.BooleanField()),
                ("respuestas", models.JSONField(default=dict)),
                ("texto_legal", models.TextField()),
                (
                    "archivo_pdf",
                    models.FileField(upload_to=pas.models.archivo_ddjj_pas_upload_to),
                ),
                ("finalizada", models.DateTimeField(blank=True, null=True)),
                (
                    "invitacion",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="declaracion",
                        to="pas.pasinvitacionddjj",
                    ),
                ),
                (
                    "municipio",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="declaraciones_juradas_pas",
                        to="core.municipio",
                    ),
                ),
                (
                    "persona",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="declaraciones_juradas",
                        to="pas.paspersona",
                    ),
                ),
                (
                    "provincia",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="declaraciones_juradas_pas",
                        to="core.provincia",
                    ),
                ),
            ],
            options={
                "verbose_name": "Declaración jurada PAS",
                "verbose_name_plural": "Declaraciones juradas PAS",
                "ordering": ["-version", "-presentada", "-id"],
            },
        ),
        migrations.AddConstraint(
            model_name="pasdeclaracionjurada",
            constraint=models.UniqueConstraint(
                fields=("persona", "version"), name="pas_ddjj_persona_version_uniq"
            ),
        ),
        migrations.AlterModelOptions(
            name="paspersona",
            options={
                "ordering": ["apellidos", "nombres", "id_persona"],
                "permissions": [
                    ("export_ddjj_tokens", "Puede exportar enlaces de DDJJ PAS")
                ],
                "verbose_name": "Persona PAS",
                "verbose_name_plural": "Personas PAS",
            },
        ),
        migrations.CreateModel(
            name="PasExportacionTokens",
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
                ("fecha", models.DateTimeField(auto_now_add=True)),
                ("cantidad", models.PositiveIntegerField()),
                (
                    "usuario",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="exportaciones_tokens_ddjj_pas",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Exportación de enlaces DDJJ PAS",
                "verbose_name_plural": "Exportaciones de enlaces DDJJ PAS",
                "ordering": ["-fecha", "-id"],
            },
        ),
        migrations.RunPython(crear_tokens_faltantes, migrations.RunPython.noop),
    ]
