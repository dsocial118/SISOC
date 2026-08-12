"""Corrección controlada de expedientes indicada en el issue #2272."""

from __future__ import annotations

import csv
import hashlib
import re
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models.functions import Upper

from admisiones.models.admisiones import Admision, AdmisionHistorial


FORMATO_EXPEDIENTE = re.compile(r"^EX-\d{4}-\d{9}- -APN-[A-Z0-9]+#[A-Z0-9]+$")
ENCABEZADOS_ESPERADOS = ("ID ADMISION", "Expediente Correcto")


@dataclass(frozen=True)
class CorreccionExpediente:
    """Una fila validada del manifiesto de correcciones."""

    admision_id: int
    numero_expediente: str
    fila: int


@dataclass
class ResultadoPreflight:
    """Resultado sin efectos de validar el manifiesto y la base objetivo."""

    correcciones: dict[int, CorreccionExpediente] = field(default_factory=dict)
    errores: list[str] = field(default_factory=list)
    advertencias: list[str] = field(default_factory=list)


class Command(BaseCommand):
    help = (
        "Valida y, con --apply, corrige los números de expediente del issue #2272. "
        "La ejecución con escritura requiere una ventana sin altas ni ediciones."
    )

    manifest_sha256 = "CF9899747608D668B7B17FF41791E77E5D473B56D62EE1FD71CFDAF854387403"

    def add_arguments(self, parser):
        modo = parser.add_mutually_exclusive_group()
        modo.add_argument(
            "--apply",
            action="store_true",
            help="Aplica la corrección tras un preflight exitoso.",
        )
        modo.add_argument(
            "--verify",
            action="store_true",
            help="Verifica que Técnicos y Legales coincidan con el manifiesto.",
        )
        parser.add_argument(
            "--database",
            default="default",
            help="Alias de base de datos objetivo.",
        )

    def get_manifest_path(self):
        return (
            Path(__file__).resolve().parents[2] / "data" / "issue_2272_expedientes.csv"
        )

    def handle(self, *args, **options):
        database = options["database"]
        aplicar = options.get("apply", False)
        verificar = options.get("verify", False)
        resultado = self._preflight(database=database, bloquear_filas=False)
        self._mostrar_resultado_preflight(resultado)
        self._detener_si_hay_errores(resultado)

        if verificar:
            errores = self._verificar_correcciones(resultado.correcciones, database)
            if errores:
                for error in errores:
                    self.stderr.write(self.style.ERROR(error))
                raise CommandError(
                    "Verificación de corrección #2272 rechazada; "
                    "hay campos sin sincronizar."
                )
            self.stdout.write(
                self.style.SUCCESS(
                    "Verificación #2272 correcta: Técnicos y Legales coinciden "
                    "con el manifiesto."
                )
            )
            return

        if not aplicar:
            self.stdout.write(
                self.style.SUCCESS(
                    "Preflight correcto. No se modificaron datos; use --apply "
                    "durante una ventana sin escrituras para ejecutar la corrección."
                )
            )
            return

        with transaction.atomic(using=database):
            resultado = self._preflight(database=database, bloquear_filas=True)
            self._detener_si_hay_errores(resultado)
            actualizadas, historial_creado = self._aplicar_correcciones(
                resultado.correcciones, database
            )

        self.stdout.write(
            self.style.SUCCESS(
                "Corrección #2272 aplicada: "
                f"{actualizadas} admisiones actualizadas; "
                f"{historial_creado} registros de historial creados."
            )
        )

    def _preflight(self, *, database, bloquear_filas):
        resultado = self._cargar_y_validar_manifiesto()
        if resultado.errores:
            return resultado

        queryset = Admision.objects.using(database).filter(
            pk__in=resultado.correcciones
        )
        if bloquear_filas:
            queryset = queryset.select_for_update()
        admisiones = {admision.pk: admision for admision in queryset}

        ids_faltantes = sorted(set(resultado.correcciones) - set(admisiones))
        if ids_faltantes:
            resultado.errores.append(
                "No existen todas las admisiones objetivo "
                f"({len(ids_faltantes)} faltantes; ejemplo: {ids_faltantes[:5]})."
            )
            return resultado

        propietarios_actuales = self._obtener_propietarios_actuales(
            resultado.correcciones, database
        )
        propietarios_esperados = {
            correccion.numero_expediente.upper(): correccion.admision_id
            for correccion in resultado.correcciones.values()
        }
        ids_objetivo = set(resultado.correcciones)
        for numero_expediente, propietarios in propietarios_actuales.items():
            propietario_esperado = propietarios_esperados[numero_expediente]
            propietarios_en_conflicto = []
            for propietario in propietarios:
                if propietario == propietario_esperado:
                    continue
                correccion_del_propietario = resultado.correcciones.get(propietario)
                if (
                    propietario in ids_objetivo
                    and correccion_del_propietario.numero_expediente.upper()
                    != numero_expediente
                ):
                    continue
                propietarios_en_conflicto.append(propietario)
            if propietarios_en_conflicto:
                resultado.errores.append(
                    "El expediente objetivo ya está asociado a otra admisión "
                    f"(expediente de la admisión {propietario_esperado}; "
                    "asociado actualmente a "
                    f"{propietarios_en_conflicto})."
                )

        return resultado

    def _cargar_y_validar_manifiesto(self):
        resultado = ResultadoPreflight()
        manifest_path = self.get_manifest_path()
        contenido = manifest_path.read_bytes()
        checksum = self._calcular_checksum(contenido)
        if checksum != self.manifest_sha256:
            resultado.errores.append(
                "El manifiesto no coincide con el checksum versionado; "
                "no se aplicará una fuente de datos no auditada."
            )
            return resultado

        with manifest_path.open(encoding="utf-8", newline="") as manifest:
            reader = csv.DictReader(manifest)
            if tuple(reader.fieldnames or ()) != ENCABEZADOS_ESPERADOS:
                resultado.errores.append(
                    "El manifiesto no tiene los encabezados esperados: "
                    f"{', '.join(ENCABEZADOS_ESPERADOS)}."
                )
                return resultado

            filas = []
            for numero_fila, fila in enumerate(reader, start=2):
                try:
                    admision_id = int((fila["ID ADMISION"] or "").strip())
                except ValueError:
                    resultado.errores.append(
                        f"La fila {numero_fila} no tiene un ID de admisión válido."
                    )
                    continue
                numero_expediente = (fila["Expediente Correcto"] or "").strip()
                if not numero_expediente:
                    resultado.errores.append(
                        f"La fila {numero_fila} no tiene número de expediente."
                    )
                    continue
                filas.append(
                    CorreccionExpediente(
                        admision_id=admision_id,
                        numero_expediente=numero_expediente,
                        fila=numero_fila,
                    )
                )

        for correccion in filas:
            anterior = resultado.correcciones.get(correccion.admision_id)
            if anterior is None:
                resultado.correcciones[correccion.admision_id] = correccion
            elif anterior.numero_expediente == correccion.numero_expediente:
                resultado.advertencias.append(
                    f"Fila {correccion.fila} repetida para la admisión "
                    f"{correccion.admision_id}; se consolidó una sola corrección."
                )
            else:
                resultado.errores.append(
                    "La admisión "
                    f"{correccion.admision_id} tiene expedientes distintos "
                    f"en las filas {anterior.fila} y {correccion.fila}."
                )

        expedientes_por_admision = defaultdict(list)
        for correccion in resultado.correcciones.values():
            expedientes_por_admision[correccion.numero_expediente.upper()].append(
                correccion.admision_id
            )
        for admisiones in expedientes_por_admision.values():
            if len(admisiones) > 1:
                resultado.errores.append(
                    "El manifiesto asigna el mismo expediente a más de una admisión: "
                    f"{sorted(admisiones)}."
                )

        invalidas = [
            correccion.admision_id
            for correccion in resultado.correcciones.values()
            if not FORMATO_EXPEDIENTE.fullmatch(correccion.numero_expediente)
        ]
        if invalidas:
            resultado.errores.append(
                "Hay "
                f"{len(invalidas)} expedientes que no cumplen el formato vigente "
                "de #2076 (EX-AAAA-NNNNNNNNN- -APN-REPARTICION#ORGANISMO; "
                f"ejemplos de admisión: {invalidas[:5]})."
            )

        return resultado

    @staticmethod
    def _calcular_checksum(contenido):
        contenido_normalizado = contenido.replace(b"\r\n", b"\n")
        return hashlib.sha256(contenido_normalizado).hexdigest().upper()

    @staticmethod
    def _obtener_propietarios_actuales(correcciones, database):
        expedientes = {
            correccion.numero_expediente.upper() for correccion in correcciones.values()
        }
        propietarios = defaultdict(set)
        filas = (
            Admision.objects.using(database)
            .exclude(num_expediente__isnull=True)
            .exclude(num_expediente="")
            .annotate(numero_normalizado=Upper("num_expediente"))
            .filter(numero_normalizado__in=expedientes)
            .values_list("pk", "numero_normalizado")
        )
        for admision_id, numero_expediente in filas:
            propietarios[numero_expediente].add(admision_id)
        return propietarios

    @staticmethod
    def _verificar_correcciones(correcciones, database):
        with transaction.atomic(using=database):
            valores_actuales = {
                admision_id: (num_expediente, legales_num_if)
                for admision_id, num_expediente, legales_num_if in (
                    Admision.objects.using(database)
                    .select_for_update()
                    .filter(pk__in=correcciones)
                    .values_list("pk", "num_expediente", "legales_num_if")
                )
            }
        ids_faltantes = sorted(set(correcciones) - set(valores_actuales))
        if ids_faltantes:
            return [
                "La verificación no encontró todas las admisiones objetivo "
                f"({len(ids_faltantes)} faltantes; ejemplo: {ids_faltantes[:5]})."
            ]

        inconsistencias = []
        for admision_id, valores in valores_actuales.items():
            num_expediente, legales_num_if = valores
            esperado = correcciones[admision_id].numero_expediente
            if num_expediente != esperado or legales_num_if != esperado:
                inconsistencias.append(admision_id)

        if inconsistencias:
            return [
                "La verificación encontró "
                f"{len(inconsistencias)} admisiones sin sincronizar; "
                f"ejemplos: {inconsistencias[:5]}."
            ]
        return []

    @staticmethod
    def _aplicar_correcciones(correcciones, database):
        admisiones = list(
            Admision.objects.using(database)
            .select_for_update()
            .filter(pk__in=correcciones)
            .order_by("pk")
        )
        historial = []
        actualizadas = []

        for admision in admisiones:
            numero_nuevo = correcciones[admision.pk].numero_expediente
            if admision.num_expediente != numero_nuevo:
                historial.append(
                    AdmisionHistorial(
                        admision=admision,
                        campo="Número de expediente",
                        valor_anterior=admision.num_expediente,
                        valor_nuevo=numero_nuevo,
                        usuario=None,
                    )
                )
            if admision.legales_num_if != numero_nuevo:
                historial.append(
                    AdmisionHistorial(
                        admision=admision,
                        campo="Expediente en Legales",
                        valor_anterior=admision.legales_num_if,
                        valor_nuevo=numero_nuevo,
                        usuario=None,
                    )
                )
            if (
                admision.num_expediente == numero_nuevo
                and admision.legales_num_if == numero_nuevo
            ):
                continue
            admision.num_expediente = numero_nuevo
            admision.legales_num_if = numero_nuevo
            actualizadas.append(admision)

        if actualizadas:
            Admision.objects.using(database).bulk_update(
                actualizadas,
                ["num_expediente", "legales_num_if"],
                batch_size=200,
            )
        if historial:
            AdmisionHistorial.objects.using(database).bulk_create(
                historial,
                batch_size=200,
            )

        return len(actualizadas), len(historial)

    def _mostrar_resultado_preflight(self, resultado):
        for advertencia in resultado.advertencias:
            self.stdout.write(self.style.WARNING(advertencia))
        for error in resultado.errores:
            self.stderr.write(self.style.ERROR(error))

    @staticmethod
    def _detener_si_hay_errores(resultado):
        if resultado.errores:
            raise CommandError(
                "Preflight de corrección #2272 rechazado; no se modificaron datos."
            )
