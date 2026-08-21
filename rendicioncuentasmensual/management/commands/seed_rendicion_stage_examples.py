"""Crea escenarios locales para validar permisos y acciones por etapa."""

from datetime import date
from typing import NamedTuple

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from comedores.models import Comedor
from rendicioncuentasmensual.models import (
    DocumentacionAdjunta,
    RendicionCuentaMensual,
    SolicitudDocumentoFaltante,
)


class StageScenario(NamedTuple):
    username: str
    group_name: str
    permission_codename: str
    nombre: str
    estado: str
    etapa: str
    subestado: str
    numero: int


class Command(BaseCommand):
    help = "Crea usuarios, grupos y rendiciones QA para probar las cuatro etapas."

    SCENARIOS = (
        StageScenario(
            "qa_rendicion_territorial",
            "QA Rendiciones - Territorial",
            "manage_territorial_stage",
            "[QA ETAPAS] 1 - Revisión Territorial pendiente",
            "revision",
            "revision_documentacion",
            "pendiente",
            1,
        ),
        StageScenario(
            "qa_rendicion_revision_auditoria",
            "QA Rendiciones - Revisión Auditoría",
            "manage_auditoria_review_stage",
            "[QA ETAPAS] 2 - Revisión de Auditoría pendiente",
            "revision",
            "revision_auditoria",
            "pendiente",
            2,
        ),
        StageScenario(
            "qa_rendicion_auditoria",
            "QA Rendiciones - Auditoría",
            "manage_auditoria_stage",
            "[QA ETAPAS] 3 - Auditoría pendiente",
            "finalizada",
            "auditoria",
            "pendiente",
            3,
        ),
        StageScenario(
            "qa_rendicion_regularizacion",
            "QA Rendiciones - Regularización",
            "manage_regularizacion_stage",
            "[QA ETAPAS] 4 - Auditoría finalizada con observaciones",
            "finalizada",
            "auditoria",
            "finalizada_con_observaciones",
            4,
        ),
    )

    def add_arguments(self, parser):
        parser.add_argument("--comedor-id", type=int, required=True)
        parser.add_argument("--password", required=True)

    @transaction.atomic
    def handle(self, *args, **options):
        password = options["password"]
        if len(password) < 12:
            raise CommandError("La contraseña QA debe tener al menos 12 caracteres.")

        try:
            comedor = Comedor.objects.get(pk=options["comedor_id"])
        except Comedor.DoesNotExist as exc:
            raise CommandError("El espacio indicado no existe.") from exc

        user_model = get_user_model()
        for scenario in self.SCENARIOS:
            permission = Permission.objects.get(
                content_type__app_label="rendicioncuentasmensual",
                codename=scenario.permission_codename,
            )
            group, _ = Group.objects.get_or_create(name=scenario.group_name)
            group.permissions.set([permission])

            user, _ = user_model.objects.get_or_create(username=scenario.username)
            user.email = f"{scenario.username}@example.invalid"
            user.is_active = True
            user.set_password(password)
            user.save()
            user.groups.set([group])

            rendicion, _ = RendicionCuentaMensual.objects.update_or_create(
                nombre=scenario.nombre,
                defaults={
                    "comedor": comedor,
                    "proyecto": comedor.proyecto,
                    "mes": scenario.numero,
                    "anio": 2026,
                    "convenio": "P01",
                    "numero_rendicion": scenario.numero,
                    "periodo_inicio": date(2026, scenario.numero, 1),
                    "periodo_fin": date(2026, scenario.numero, 28),
                    "estado": scenario.estado,
                    "etapa_proceso": scenario.etapa,
                    "subestado_proceso": scenario.subestado,
                    "linea_programatica": RendicionCuentaMensual.LINEA_TRADICIONAL,
                },
            )
            DocumentacionAdjunta.objects.filter(
                rendicion_cuenta_mensual=rendicion,
                nombre__startswith="[QA ETAPAS]",
            ).delete()
            SolicitudDocumentoFaltante.objects.filter(rendicion=rendicion).delete()
            if scenario.etapa in {"revision_documentacion", "revision_auditoria"}:
                DocumentacionAdjunta.objects.create(
                    rendicion_cuenta_mensual=rendicion,
                    nombre="[QA ETAPAS] Documento presentado",
                    categoria=DocumentacionAdjunta.CATEGORIA_FORMULARIO_II,
                    estado=DocumentacionAdjunta.ESTADO_PRESENTADO,
                    archivo=ContentFile(b"Documento QA", name="documento_qa.txt"),
                )
            self.stdout.write(
                self.style.SUCCESS(
                    f"{scenario.username} | {scenario.group_name} | "
                    f"rendición {rendicion.pk}"
                )
            )
