# celiaquia/services/cupo_service.py
from __future__ import annotations

import logging
from typing import Dict

from django.db import transaction
from django.core.exceptions import ValidationError
from django.db.models import F

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
    # -------------------- MÉTRICAS Y LISTADOS --------------------

    @staticmethod
    def metrics_por_provincia(provincia: Provincia) -> Dict[str, int]:
        """
        Devuelve: total_asignado, usados, disponibles y fuera (lista de espera).
        """
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
        """
        Titulares activos que ocupan cupo.
        """
        return ExpedienteCiudadano.objects.filter(
            expediente__usuario_provincia__profile__provincia=provincia,
            revision_tecnico=RevisionTecnico.APROBADO,
            resultado_sintys=ResultadoSintys.MATCH,
            estado_cupo=EstadoCupo.DENTRO,
            es_titular_activo=True,
        )

    @staticmethod
    def lista_suspendidos_por_provincia(provincia: Provincia):
        """
        Titulares suspendidos: mantienen estado_cupo=DENTRO (cupo ocupado) pero es_titular_activo=False.
        """
        return ExpedienteCiudadano.objects.filter(
            expediente__usuario_provincia__profile__provincia=provincia,
            estado_cupo=EstadoCupo.DENTRO,
            es_titular_activo=False,
        )

    @staticmethod
    def lista_fuera_de_cupo_por_expediente(expediente_id: int):
        """
        Lista de espera de un expediente (estado_cupo=FUERA).
        """
        return ExpedienteCiudadano.objects.filter(
            expediente_id=expediente_id,
            estado_cupo=EstadoCupo.FUERA,
        )

    # -------------------- CONFIGURAR TOTAL --------------------

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

    # -------------------- OPERACIONES DE CUPO --------------------

    @staticmethod
    @transaction.atomic
    def reservar_slot(*, legajo: ExpedienteCiudadano, usuario, motivo: str = "") -> bool:
        """
        Intenta ocupar un cupo para el legajo.
        Reglas:
        - Sólo si (APROBADO + MATCH).
        - Si el ciudadano ya ocupa un cupo DENTRO en la provincia (activo o suspendido), NO se reserva otro:
          este legajo queda FUERA (lista de espera) y no cambia 'usados'.
        - Si no hay disponibles, queda FUERA (lista de espera) y no cambia 'usados'.
        - Si se puede, incrementa 'usados', marca DENTRO + es_titular_activo=True y registra ALTA (+1).
        """
        legajo = (
            ExpedienteCiudadano.objects.select_for_update()
            .select_related("expediente", "expediente__usuario_provincia", "expediente__usuario_provincia__profile")
            .get(pk=legajo.pk)
        )

        # Validar que califica para cupo
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

        # Si ya está dentro y activo, nada para hacer
        if legajo.estado_cupo == EstadoCupo.DENTRO and legajo.es_titular_activo:
            return True

        # Si el ciudadano YA ocupa un cupo DENTRO en la provincia (activo o suspendido), no se puede reservar otro
        ya_ocupa = ExpedienteCiudadano.objects.filter(
            ciudadano_id=legajo.ciudadano_id,
            expediente__usuario_provincia__profile__provincia=provincia,
            estado_cupo=EstadoCupo.DENTRO,
        ).exclude(pk=legajo.pk).exists()
        if ya_ocupa:
            if legajo.estado_cupo != EstadoCupo.FUERA or legajo.es_titular_activo:
                legajo.estado_cupo = EstadoCupo.FUERA
                legajo.es_titular_activo = False
                legajo.save(update_fields=["estado_cupo", "es_titular_activo", "modificado_en"])
            return False

        # Chequear disponibles
        disponibles = int(pc.total_asignado or 0) - int(pc.usados or 0)
        if disponibles <= 0:
            if legajo.estado_cupo != EstadoCupo.FUERA or legajo.es_titular_activo:
                legajo.estado_cupo = EstadoCupo.FUERA
                legajo.es_titular_activo = False
                legajo.save(update_fields=["estado_cupo", "es_titular_activo", "modificado_en"])
            return False

        # Ocupar cupo
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
            motivo=(motivo or "").strip()[:255],
            usuario=usuario,
        )
        logger.info("Cupo ALTA: provincia=%s usados=%s legajo=%s", provincia, pc.usados, legajo.pk)
        return True

    @staticmethod
    @transaction.atomic
    def suspender_slot(*, legajo: ExpedienteCiudadano, usuario, motivo: str = "") -> bool:
        """
        Suspende el legajo manteniendo el cupo ocupado.
        - NO modifica ProvinciaCupo.usados.
        - Deja estado_cupo=DENTRO y es_titular_activo=False.
        - Registra movimiento SUSPENDIDO (delta=0).
        """
        legajo = (
            ExpedienteCiudadano.objects.select_for_update()
            .select_related("expediente", "expediente__usuario_provincia", "expediente__usuario_provincia__profile")
            .get(pk=legajo.pk)
        )
        provincia = getattr(legajo.expediente.usuario_provincia.profile, "provincia", None)
        if not provincia:
            raise ValidationError("El legajo no tiene provincia asociada al usuario del expediente.")

        # Sólo si tiene cupo DENTRO (activo o ya suspendido)
        if legajo.estado_cupo != EstadoCupo.DENTRO:
            # no cambia contadores ni estados NO_EVAL/FUERA aquí
            return False

        if legajo.es_titular_activo:
            legajo.es_titular_activo = False
            legajo.save(update_fields=["es_titular_activo", "modificado_en"])

            CupoMovimiento.objects.create(
                provincia=provincia,
                expediente=legajo.expediente,
                legajo=legajo,
                tipo=TipoMovimientoCupo.SUSPENDIDO,
                delta=0,
                motivo=(motivo or "Suspensión de titular").strip()[:255],
                usuario=usuario,
            )
            logger.info("Cupo SUSPENDIDO: provincia=%s usados (sin cambio) legajo=%s", provincia, legajo.pk)

        return True

    @staticmethod
    @transaction.atomic
    def liberar_slot(*, legajo: ExpedienteCiudadano, usuario, motivo: str = "") -> bool:
        """
        Libera definitivamente el cupo (BAJA).
        - Si el legajo estaba DENTRO (activo o suspendido), disminuye ProvinciaCupo.usados en 1.
        - Pone estado_cupo=NO_EVAL y es_titular_activo=False.
        - Registra movimiento BAJA (delta=-1).
        """
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

        # Sólo si estaba DENTRO se descuenta
        if legajo.estado_cupo != EstadoCupo.DENTRO:
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
            motivo=(motivo or "Baja de titular").strip()[:255],
            usuario=usuario,
        )
        logger.info("Cupo BAJA: provincia=%s usados=%s legajo=%s", provincia, pc.usados, legajo.pk)
        return True
    
    @staticmethod
    @transaction.atomic
    def reactivar_slot(*, legajo: ExpedienteCiudadano, usuario, motivo: str = "") -> bool:
        """
        Reactiva un legajo suspendido manteniendo el cupo ocupado.
        - NO modifica ProvinciaCupo.usados.
        - Requiere estado_cupo=DENTRO y es_titular_activo=False.
        - Deja es_titular_activo=True.
        - Registra movimiento AJUSTE (delta=0).
        """
        legajo = (
            ExpedienteCiudadano.objects.select_for_update()
            .select_related("expediente", "expediente__usuario_provincia", "expediente__usuario_provincia__profile")
            .get(pk=legajo.pk)
        )
        provincia = getattr(legajo.expediente.usuario_provincia.profile, "provincia", None)
        if not provincia:
            raise ValidationError("El legajo no tiene provincia asociada al usuario del expediente.")

        # Debe estar dentro de cupo y NO activo
        if legajo.estado_cupo != EstadoCupo.DENTRO or legajo.es_titular_activo:
            return False

        legajo.es_titular_activo = True
        legajo.save(update_fields=["es_titular_activo", "modificado_en"])

        CupoMovimiento.objects.create(
            provincia=provincia,
            expediente=legajo.expediente,
            legajo=legajo,
            tipo=TipoMovimientoCupo.REACTIVACION,  # delta 0
            delta=0,
            motivo=(motivo or "Reactivación de titular").strip()[:255],
            usuario=usuario,
        )
        logger.info("Cupo REACTIVADO (ajuste): provincia=%s legajo=%s", provincia, legajo.pk)
        return True

