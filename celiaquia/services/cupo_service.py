from __future__ import annotations

import logging
from typing import Dict

from django.db import transaction
from django.core.exceptions import ValidationError
from django.db.models import F, Exists, OuterRef

from ciudadanos.models import Provincia
from celiaquia.models import (
    ExpedienteCiudadano,
    ProvinciaCupo,
    CupoMovimiento,
    EstadoCupo,
    TipoMovimientoCupo,
    RevisionTecnico,
    ResultadoSintys,
)

logger = logging.getLogger(__name__)


class CupoNoConfigurado(Exception):
    pass


class CupoService:
    @staticmethod
    def metrics_por_provincia(provincia: Provincia) -> Dict[str, int]:
        try:
            pc = ProvinciaCupo.objects.only("total_asignado", "usados").get(provincia=provincia)
        except ProvinciaCupo.DoesNotExist:
            raise CupoNoConfigurado(f"La provincia '{provincia}' no tiene cupo configurado.")
        total = int(pc.total_asignado or 0)
        usados = int(pc.usados or 0)
        disponibles = max(total - usados, 0)
        fuera = ExpedienteCiudadano.objects.filter(
            expediente__usuario_provincia__profile__provincia=provincia,
            estado_cupo=EstadoCupo.FUERA,
            es_titular_activo=False,
        ).count()
        return {
            "total_asignado": total,
            "usados": usados,
            "disponibles": disponibles,
            "fuera": int(fuera),
        }

    @staticmethod
    def lista_ocupados_por_provincia(provincia: Provincia):
        return ExpedienteCiudadano.objects.filter(
            expediente__usuario_provincia__profile__provincia=provincia,
            revision_tecnico=RevisionTecnico.APROBADO,
            resultado_sintys=ResultadoSintys.MATCH,
            estado_cupo=EstadoCupo.DENTRO,
            es_titular_activo=True,
        )

    @staticmethod
    def lista_fuera_de_cupo_por_expediente(expediente_id: int):
        return ExpedienteCiudadano.objects.filter(
            expediente_id=expediente_id,
            estado_cupo=EstadoCupo.FUERA,
        )

    @staticmethod
    def configurar_total(provincia: Provincia, total_asignado: int, usuario=None) -> ProvinciaCupo:
        try:
            total = int(total_asignado)
        except Exception:
            raise ValidationError("El total asignado debe ser un entero válido.")
        if total < 0:
            raise ValidationError("El total asignado debe ser un entero ≥ 0.")
        pc, created = ProvinciaCupo.objects.get_or_create(
            provincia=provincia,
            defaults={"total_asignado": total},
        )
        if not created:
            pc.total_asignado = total
            pc.save(update_fields=["total_asignado"])
        return pc

    @staticmethod
    @transaction.atomic
    def reservar_slot(*, legajo: ExpedienteCiudadano, usuario, motivo: str = "") -> bool:
        legajo = (
            ExpedienteCiudadano.objects.select_for_update()
            .select_related("expediente", "expediente__usuario_provincia", "expediente__usuario_provincia__profile")
            .get(pk=legajo.pk)
        )

        if not (legajo.revision_tecnico == RevisionTecnico.APROBADO and legajo.resultado_sintys == ResultadoSintys.MATCH):
            if legajo.estado_cupo != EstadoCupo.NO_EVAL or legajo.es_titular_activo:
                legajo.estado_cupo = EstadoCupo.NO_EVAL
                legajo.es_titular_activo = False
                legajo.save(update_fields=["estado_cupo", "es_titular_activo", "modificado_en"])
            return False

        provincia = getattr(legajo.expediente.usuario_provincia.profile, "provincia", None)
        if not provincia:
            raise ValidationError("El legajo no tiene provincia asociada al usuario del expediente.")

        try:
            pc = ProvinciaCupo.objects.select_for_update().only("id", "usados", "total_asignado").get(provincia=provincia)
        except ProvinciaCupo.DoesNotExist:
            raise CupoNoConfigurado(f"La provincia '{provincia}' no tiene cupo configurado.")

        if legajo.estado_cupo == EstadoCupo.DENTRO and legajo.es_titular_activo:
            return True

        ya_ocupa = ExpedienteCiudadano.objects.filter(
            ciudadano_id=legajo.ciudadano_id,
            expediente__usuario_provincia__profile__provincia=provincia,
            estado_cupo=EstadoCupo.DENTRO,
            es_titular_activo=True,
        ).exclude(pk=legajo.pk).exists()
        if ya_ocupa:
            if legajo.estado_cupo != EstadoCupo.FUERA or legajo.es_titular_activo:
                legajo.estado_cupo = EstadoCupo.FUERA
                legajo.es_titular_activo = False
                legajo.save(update_fields=["estado_cupo", "es_titular_activo", "modificado_en"])
            return False

        disponibles = int(pc.total_asignado or 0) - int(pc.usados or 0)
        if disponibles <= 0:
            if legajo.estado_cupo != EstadoCupo.FUERA or legajo.es_titular_activo:
                legajo.estado_cupo = EstadoCupo.FUERA
                legajo.es_titular_activo = False
                legajo.save(update_fields=["estado_cupo", "es_titular_activo", "modificado_en"])
            return False

        ProvinciaCupo.objects.filter(pk=pc.pk).update(usados=F("usados") + 1)
        pc.refresh_from_db(fields=["usados"])

        legajo.estado_cupo = EstadoCupo.DENTRO
        legajo.es_titular_activo = True
        legajo.save(update_fields=["estado_cupo", "es_titular_activo", "modificado_en"])

        CupoMovimiento.objects.create(
            provincia=provincia,
            expediente=legajo.expediente,
            legajo=legajo,
            tipo=TipoMovimientoCupo.ALTA,
            delta=+1,
            motivo=motivo[:255],
            usuario=usuario,
        )
        logger.info("Cupo ALTA: provincia=%s usados=%s legajo=%s", provincia, pc.usados, legajo.pk)
        return True

    @staticmethod
    @transaction.atomic
    def liberar_slot(*, legajo: ExpedienteCiudadano, usuario, motivo: str = "") -> bool:
        legajo = (
            ExpedienteCiudadano.objects.select_for_update()
            .select_related("expediente", "expediente__usuario_provincia", "expediente__usuario_provincia__profile")
            .get(pk=legajo.pk)
        )
        provincia = getattr(legajo.expediente.usuario_provincia.profile, "provincia", None)
        if not provincia:
            raise ValidationError("El legajo no tiene provincia asociada al usuario del expediente.")

        try:
            pc = ProvinciaCupo.objects.select_for_update().only("id", "usados").get(provincia=provincia)
        except ProvinciaCupo.DoesNotExist:
            raise CupoNoConfigurado(f"La provincia '{provincia}' no tiene cupo configurado.")

        if not (legajo.estado_cupo == EstadoCupo.DENTRO and legajo.es_titular_activo):
            if legajo.estado_cupo != EstadoCupo.NO_EVAL or legajo.es_titular_activo:
                legajo.estado_cupo = EstadoCupo.NO_EVAL
                legajo.es_titular_activo = False
                legajo.save(update_fields=["estado_cupo", "es_titular_activo", "modificado_en"])
            return False

        if int(pc.usados or 0) > 0:
            ProvinciaCupo.objects.filter(pk=pc.pk).update(usados=F("usados") - 1)
            pc.refresh_from_db(fields=["usados"])

        legajo.estado_cupo = EstadoCupo.NO_EVAL
        legajo.es_titular_activo = False
        legajo.save(update_fields=["estado_cupo", "es_titular_activo", "modificado_en"])

        CupoMovimiento.objects.create(
            provincia=provincia,
            expediente=legajo.expediente,
            legajo=legajo,
            tipo=TipoMovimientoCupo.BAJA,
            delta=-1,
            motivo=motivo[:255],
            usuario=usuario,
        )
        logger.info("Cupo BAJA: provincia=%s usados=%s legajo=%s", provincia, pc.usados, legajo.pk)
        return True
