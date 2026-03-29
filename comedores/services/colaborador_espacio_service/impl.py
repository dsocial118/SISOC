from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from django.utils import timezone
from django.db import transaction

from ciudadanos.models import Ciudadano
from comedores.models import AuditColaboradorEspacio, ColaboradorEspacio
from comedores.services.comedor_service import ComedorService


class ColaboradorEspacioService:
    SEXO_LABELS = {
        "M": "Masculino",
        "F": "Femenino",
        "X": "X",
    }

    @staticmethod
    def _split_cuil(cuil_value):
        digits = "".join(ch for ch in str(cuil_value or "") if ch.isdigit())
        if len(digits) != 11:
            return None, None
        return digits[:2], digits[-1]

    @staticmethod
    def build_preview_from_ciudadano(ciudadano: Ciudadano) -> dict:
        prefijo_cuil, sufijo_cuil = ColaboradorEspacioService._split_cuil(
            ciudadano.cuil_cuit
        )
        return {
            "apellido": ciudadano.apellido,
            "nombre": ciudadano.nombre,
            "dni": ciudadano.documento,
            "prefijo_cuil": prefijo_cuil,
            "cuil_cuit": ciudadano.cuil_cuit,
            "sufijo_cuil": sufijo_cuil,
            "sexo": getattr(ciudadano.sexo, "sexo", None),
            "fecha_nacimiento": ciudadano.fecha_nacimiento,
            "edad": ciudadano.edad,
        }

    @staticmethod
    def build_preview_from_renaper_data(renaper_data: dict) -> dict:
        cuil = renaper_data.get("cuil_cuit") or renaper_data.get("cuil")
        prefijo_cuil, sufijo_cuil = ColaboradorEspacioService._split_cuil(cuil)
        return {
            "apellido": renaper_data.get("apellido"),
            "nombre": renaper_data.get("nombre"),
            "dni": renaper_data.get("documento") or renaper_data.get("dni"),
            "prefijo_cuil": prefijo_cuil,
            "cuil_cuit": cuil,
            "sufijo_cuil": sufijo_cuil,
            "sexo": ColaboradorEspacioService.SEXO_LABELS.get(
                renaper_data.get("genero")
            )
            or renaper_data.get("sexo_display")
            or renaper_data.get("sexo"),
            "fecha_nacimiento": renaper_data.get("fecha_nacimiento"),
            "edad": ColaboradorEspacioService._calculate_age(
                renaper_data.get("fecha_nacimiento")
            ),
        }

    @staticmethod
    def _calculate_age(fecha_nacimiento):
        if not fecha_nacimiento:
            return None
        try:
            return Ciudadano(fecha_nacimiento=fecha_nacimiento).edad
        except Exception:
            return None

    @staticmethod
    def _build_create_response(success, message, colaborador=None, ciudadano=None):
        return {
            "success": success,
            "message": message,
            "colaborador": colaborador,
            "ciudadano": ciudadano,
        }

    @staticmethod
    def _json_safe(value):
        if isinstance(value, dict):
            return {
                str(key): ColaboradorEspacioService._json_safe(val)
                for key, val in value.items()
            }
        if isinstance(value, list):
            return [ColaboradorEspacioService._json_safe(item) for item in value]
        if isinstance(value, tuple):
            return [ColaboradorEspacioService._json_safe(item) for item in value]
        if isinstance(value, (datetime, date)):
            return value.isoformat()
        if isinstance(value, Decimal):
            return float(value)
        return value

    @staticmethod
    def _snapshot(colaborador: ColaboradorEspacio) -> dict:
        return {
            "id": colaborador.id,
            "comedor_id": colaborador.comedor_id,
            "ciudadano_id": colaborador.ciudadano_id,
            "genero": colaborador.genero,
            "codigo_telefono": colaborador.codigo_telefono,
            "numero_telefono": colaborador.numero_telefono,
            "fecha_alta": colaborador.fecha_alta,
            "fecha_baja": colaborador.fecha_baja,
            "actividades": list(
                colaborador.actividades.order_by("orden", "id").values_list(
                    "nombre", flat=True
                )
            ),
            "fecha_creado": colaborador.fecha_creado,
            "fecha_modificado": colaborador.fecha_modificado,
        }

    @staticmethod
    def _registrar_auditoria(
        *,
        colaborador: ColaboradorEspacio,
        actor,
        accion: str,
        snapshot_antes: dict | None = None,
        snapshot_despues: dict | None = None,
        metadata: dict | None = None,
    ):
        AuditColaboradorEspacio.objects.create(
            colaborador=colaborador,
            comedor=colaborador.comedor,
            ciudadano=colaborador.ciudadano,
            changed_by=actor if getattr(actor, "is_authenticated", False) else None,
            accion=accion,
            snapshot_antes=ColaboradorEspacioService._json_safe(snapshot_antes)
            if snapshot_antes
            else None,
            snapshot_despues=ColaboradorEspacioService._json_safe(snapshot_despues)
            if snapshot_despues
            else None,
            metadata=ColaboradorEspacioService._json_safe(metadata) if metadata else {},
        )

    @staticmethod
    def update_for_comedor(*, colaborador, actor, cleaned_data):
        colaborador_antes = (
            ColaboradorEspacio.objects.select_related("ciudadano")
            .prefetch_related("actividades")
            .get(pk=colaborador.pk)
        )
        snapshot_antes = ColaboradorEspacioService._snapshot(colaborador_antes)
        actividades = cleaned_data.pop("actividades", None)
        for field_name, value in cleaned_data.items():
            setattr(colaborador, field_name, value)
        colaborador.modificado_por = (
            actor if getattr(actor, "is_authenticated", False) else None
        )
        colaborador.save()
        if actividades is not None:
            colaborador.actividades.set(actividades)
        snapshot_despues = ColaboradorEspacioService._snapshot(colaborador)
        ColaboradorEspacioService._registrar_auditoria(
            colaborador=colaborador,
            actor=actor,
            accion=AuditColaboradorEspacio.ACCION_UPDATE,
            snapshot_antes=snapshot_antes,
            snapshot_despues=snapshot_despues,
        )
        return ColaboradorEspacioService._build_create_response(
            True,
            "Colaborador actualizado correctamente.",
            colaborador=colaborador,
            ciudadano=colaborador.ciudadano,
        )

    @staticmethod
    def soft_delete(*, colaborador, actor):
        if colaborador.fecha_baja:
            return ColaboradorEspacioService._build_create_response(
                False,
                "El colaborador ya se encuentra dado de baja.",
                colaborador=colaborador,
                ciudadano=colaborador.ciudadano,
            )
        snapshot_antes = ColaboradorEspacioService._snapshot(colaborador)
        colaborador.fecha_baja = timezone.now().date()
        colaborador.modificado_por = actor if getattr(actor, "is_authenticated", False) else None
        colaborador.save(update_fields=["fecha_baja", "modificado_por", "fecha_modificado"])
        snapshot_despues = ColaboradorEspacioService._snapshot(colaborador)
        ColaboradorEspacioService._registrar_auditoria(
            colaborador=colaborador,
            actor=actor,
            accion=AuditColaboradorEspacio.ACCION_DELETE,
            snapshot_antes=snapshot_antes,
            snapshot_despues=snapshot_despues,
        )
        return ColaboradorEspacioService._build_create_response(
            True,
            "Colaborador dado de baja correctamente.",
            colaborador=colaborador,
            ciudadano=colaborador.ciudadano,
        )

    @staticmethod
    @transaction.atomic
    def create_for_comedor(*, comedor, actor, cleaned_data, ciudadano_id=None, dni=None):
        ciudadano = None
        if ciudadano_id:
            ciudadano = Ciudadano.objects.filter(pk=ciudadano_id).first()
            if not ciudadano:
                return ColaboradorEspacioService._build_create_response(
                    False, "No se encontró el ciudadano seleccionado."
                )
        else:
            resultado = ComedorService.crear_ciudadano_desde_renaper(dni, user=actor)
            if not resultado.get("success"):
                return ColaboradorEspacioService._build_create_response(
                    False,
                    resultado.get(
                        "message", "No se pudo obtener el ciudadano desde RENAPER."
                    ),
                )
            ciudadano = resultado.get("ciudadano")

        existente = ColaboradorEspacio.objects.filter(
            comedor=comedor,
            ciudadano=ciudadano,
            fecha_baja__isnull=True,
        ).first()
        if existente:
            return ColaboradorEspacioService._build_create_response(
                False,
                "La persona ya se encuentra registrada como colaborador de este espacio.",
                colaborador=existente,
                ciudadano=ciudadano,
            )

        actividades = cleaned_data.pop("actividades", [])
        colaborador = ColaboradorEspacio.objects.create(
            comedor=comedor,
            ciudadano=ciudadano,
            creado_por=actor if getattr(actor, "is_authenticated", False) else None,
            modificado_por=actor if getattr(actor, "is_authenticated", False) else None,
            **cleaned_data,
        )
        colaborador.actividades.set(actividades)
        ColaboradorEspacioService._registrar_auditoria(
            colaborador=colaborador,
            actor=actor,
            accion=AuditColaboradorEspacio.ACCION_CREATE,
            snapshot_despues=ColaboradorEspacioService._snapshot(colaborador),
            metadata={"source": "renaper" if not ciudadano_id else "sisoc"},
        )
        return ColaboradorEspacioService._build_create_response(
            True,
            "Colaborador agregado correctamente al espacio.",
            colaborador=colaborador,
            ciudadano=ciudadano,
        )
