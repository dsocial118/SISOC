"""Revalida ciudadanos de nóminas CDI sin modificar su identidad cargada."""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from ciudadanos.models import Ciudadano
from ciudadanos.services_importacion_masiva import (
    RENAPER_SEXOS,
    SEXO_LABELS,
    is_systemic_renaper_error,
)
from ciudadanos.services_renaper_validacion import (
    build_validacion_renaper_payload,
    identidad_coincide,
)
from centrodeinfancia.models import NominaCentroInfancia
from core.services.renaper import consultar_datos_renaper

MAX_ERRORES_INESPERADOS_CONSECUTIVOS = 20

IDENTIDAD_FIELDS = (
    "documento",
    "tipo_documento",
    "apellido",
    "nombre",
    "fecha_nacimiento",
    "sexo_id",
)


def _identidad(ciudadano):
    return {field: getattr(ciudadano, field) for field in IDENTIDAD_FIELDS}


def _consultar(ciudadano):
    sexo_nombre = getattr(ciudadano.sexo, "sexo", None)
    sexo = next(
        (key for key, label in SEXO_LABELS.items() if label == sexo_nombre), None
    )
    sexos = (sexo,) if sexo else RENAPER_SEXOS
    for intento in sexos:
        try:
            result = consultar_datos_renaper(str(ciudadano.documento), intento)
        except Exception:  # pylint: disable=broad-exception-caught
            return {"success": False, "error_type": "unexpected_error"}
        if not isinstance(result, dict) or (
            result.get("success") and not isinstance(result.get("data"), dict)
        ):
            return {"success": False, "error_type": "invalid_response"}
        if result.get("success") or result.get("error_type") != "no_match":
            return result
    return result


def _payload(ciudadano, result):
    if result.get("success") and identidad_coincide(
        _identidad(ciudadano), result["data"]
    ):
        return {
            **build_validacion_renaper_payload(result),
            "motivo_no_validacion_renaper": None,
            "motivo_no_validacion_descripcion": None,
        }
    descripcion = (
        "Los datos de apellido, nombre o fecha de nacimiento no coinciden con RENAPER."
        if result.get("success")
        else "RENAPER no encontró el documento con los sexos consultados."
    )
    if result.get("error_type") == "fallecido":
        descripcion = "RENAPER reporta a la persona como fallecida."
    return {
        "estado_validacion_renaper": Ciudadano.RENAPER_NO_VALIDADO,
        "fecha_validacion_renaper": timezone.now(),
        "datos_renaper": result.get("datos_api") or result.get("data") or {},
        "motivo_no_validacion_renaper": Ciudadano.MOTIVO_NO_VALIDADO_OTRO,
        "motivo_no_validacion_descripcion": descripcion,
    }


class Command(BaseCommand):
    help = "Valida por RENAPER ciudadanos pendientes vinculados a nóminas CDI."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Consulta RENAPER y muestra contadores sin escribir en la base.",
        )
        parser.add_argument("--batch-size", type=int, default=500)
        parser.add_argument("--limit", type=int, default=None)

    # Errores inesperados seguidos; se reinicia con cualquier resultado concluyente.
    _consecutivos = 0

    @staticmethod
    def _universo():
        return (
            Ciudadano.objects.filter(
                pk__in=NominaCentroInfancia.objects.filter(
                    deleted_at__isnull=True
                ).values("ciudadano_id"),
                documento__isnull=False,
                estado_validacion_renaper=Ciudadano.RENAPER_NO_CONSULTADO,
            )
            .select_related("sexo")
            .order_by("pk")
        )

    def _procesar_ciudadano(self, ciudadano, counters):
        """Devuelve la entrada a escribir, o None si la ficha se omite."""
        counters["consultados"] += 1
        result = _consultar(ciudadano)
        error_type = result.get("error_type")
        if not result.get("success"):
            if is_systemic_renaper_error(error_type):
                counters["errores"] += 1
                raise CommandError(
                    "Error sistémico de RENAPER; se descartó el lote actual."
                )
            if error_type not in {"no_match", "fallecido"}:
                counters["omitidos"] += 1
                counters["errores"] += 1
                self._consecutivos += 1
                if self._consecutivos >= MAX_ERRORES_INESPERADOS_CONSECUTIVOS:
                    raise CommandError(
                        f"Corte por {MAX_ERRORES_INESPERADOS_CONSECUTIVOS} errores "
                        "inesperados consecutivos; se descartó el lote actual."
                    )
                return None
        self._consecutivos = 0
        payload = _payload(ciudadano, result)
        if payload["estado_validacion_renaper"] == Ciudadano.RENAPER_VALIDADO:
            counters["validados"] += 1
        else:
            counters["no_validados"] += 1
        if error_type == "fallecido":
            counters["fallecidos"] += 1
        return (ciudadano.pk, _identidad(ciudadano), payload)

    def _procesar_lote(self, lote, counters, dry_run):
        pendientes = []
        for ciudadano in lote:
            entrada = self._procesar_ciudadano(ciudadano, counters)
            if entrada is not None:
                pendientes.append(entrada)
        if dry_run:
            return
        escritos, omitidos = self._guardar(pendientes)
        counters["escritos"] += escritos
        counters["omitidos"] += omitidos

    def handle(self, *args, **options):
        batch_size = options["batch_size"]
        limit = options["limit"]
        if batch_size < 1 or (limit is not None and limit < 1):
            raise CommandError("--batch-size y --limit deben ser mayores que cero.")
        counters = {
            "consultados": 0,
            "validados": 0,
            "no_validados": 0,
            "fallecidos": 0,
            "omitidos": 0,
            "escritos": 0,
            "errores": 0,
        }
        if options["dry_run"]:
            self.stdout.write("DRY-RUN: consulta RENAPER sin escribir en la base.")
        self._consecutivos = 0
        try:
            # Cada lote se consulta sin locks y se confirma en su propia transacción.
            # Una falla descarta el lote en curso, conservando los lotes anteriores.
            for lote in self._lotes(self._universo(), batch_size, limit):
                self._procesar_lote(lote, counters, options["dry_run"])
        except CommandError:
            raise
        except Exception:  # pylint: disable=broad-exception-caught
            counters["errores"] += 1
            # No incluir mensajes externos que puedan contener datos personales.
            raise CommandError(
                "Corrida interrumpida; se conservan los lotes ya confirmados."
            ) from None
        finally:
            self._mostrar_contadores(counters)

    @staticmethod
    def _lotes(queryset, batch_size, limit):
        ultimo_pk = 0
        leidos = 0
        while limit is None or leidos < limit:
            cantidad = batch_size if limit is None else min(batch_size, limit - leidos)
            lote = list(queryset.filter(pk__gt=ultimo_pk)[:cantidad])
            if not lote:
                break
            ultimo_pk = lote[-1].pk
            leidos += len(lote)
            yield lote

    @staticmethod
    def _guardar(pendientes):
        escritos = 0
        omitidos = 0
        with transaction.atomic():
            for ciudadano_id, identidad, payload in pendientes:
                ciudadano = (
                    Ciudadano.objects.select_for_update()
                    .filter(
                        pk=ciudadano_id,
                        estado_validacion_renaper=Ciudadano.RENAPER_NO_CONSULTADO,
                    )
                    .first()
                )
                if ciudadano is None or _identidad(ciudadano) != identidad:
                    omitidos += 1
                    continue
                if not (
                    NominaCentroInfancia.objects.select_for_update()
                    .filter(ciudadano_id=ciudadano_id, deleted_at__isnull=True)
                    .exists()
                ):
                    omitidos += 1
                    continue
                Ciudadano.objects.filter(pk=ciudadano_id).update(**payload)
                escritos += 1
        return escritos, omitidos

    def _mostrar_contadores(self, counters):
        self.stdout.write(" ".join(f"{key}={value}" for key, value in counters.items()))
