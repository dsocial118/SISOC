import csv
import unicodedata
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from comedores.models import (
    Comedor,
    EstadoActividad,
    EstadoDetalle,
    EstadoProceso,
    Programas,
)
from comedores.services.estado_manager import registrar_cambio_estado

DEFAULT_PROGRAMA_ID = 3
DEFAULT_ESTADO_ACTIVIDAD = "Activo"
DEFAULT_ESTADO_PROCESO = "En ejecución"

HEADER_ALIASES = {
    "comedor_id": "comedor_id",
    "comedor": "comedor_id",
    "id": "comedor_id",
    "sisoc_id": "comedor_id",
}
REQUIRED_HEADERS = {"comedor_id"}


class Command(BaseCommand):
    """
    Actualiza programa y estado general (actividad/subestado) de comedores desde un CSV.
    """

    help = (
        "Actualiza programa y último estado (Actividad/Subestado) para comedores "
        "listados en un CSV con columna 'comedor_id'."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "csv_path",
            help="Ruta del archivo CSV con la columna 'comedor_id'.",
        )
        parser.add_argument(
            "--programa-id",
            type=int,
            default=DEFAULT_PROGRAMA_ID,
            help=f"ID del programa a asignar. Por defecto {DEFAULT_PROGRAMA_ID}.",
        )
        parser.add_argument(
            "--estado-actividad",
            default=DEFAULT_ESTADO_ACTIVIDAD,
            help=(
                "Nombre del EstadoActividad a aplicar. "
                f"Por defecto '{DEFAULT_ESTADO_ACTIVIDAD}'."
            ),
        )
        parser.add_argument(
            "--estado-proceso",
            dest="estado_proceso",
            default=DEFAULT_ESTADO_PROCESO,
            help=(
                "Nombre del EstadoProceso (subestado) a aplicar. "
                f"Por defecto '{DEFAULT_ESTADO_PROCESO}'."
            ),
        )
        parser.add_argument(
            "--subestado-proceso",
            dest="estado_proceso",
            help="Alias de --estado-proceso.",
        )
        parser.add_argument(
            "--estado-detalle",
            default="",
            help="Nombre del EstadoDetalle (motivo) a aplicar. Opcional.",
        )
        parser.add_argument(
            "--delimiter",
            default=",",
            help="Separador de columnas del CSV. Por defecto ','.",
        )
        parser.add_argument(
            "--encoding",
            default="utf-8",
            help="Encoding del CSV. Por defecto 'utf-8'.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            dest="dry_run",
            help="Muestra los cambios sin persistirlos en la base de datos.",
        )

    def handle(self, *args, **options):
        csv_path = Path(options["csv_path"]).expanduser()
        delimiter = options["delimiter"] or ","
        encoding = options["encoding"] or "utf-8"
        dry_run = options["dry_run"]

        if not csv_path.exists():
            raise CommandError(f"El archivo '{csv_path}' no existe.")
        if not csv_path.is_file():
            raise CommandError(f"'{csv_path}' no es un archivo válido.")

        programa = self._resolve_programa(options["programa_id"])
        actividad = self._resolve_estado_actividad(options["estado_actividad"])
        proceso = self._resolve_estado_proceso(actividad, options["estado_proceso"])
        detalle_label = (options.get("estado_detalle") or "").strip()
        detalle = (
            self._resolve_estado_detalle(proceso, detalle_label) if detalle_label else None
        )

        stats = {
            "rows": 0,
            "applied": 0,
            "skipped": 0,
            "errors": 0,
            "programa_updates": 0,
            "programa_skipped": 0,
            "estado_updates": 0,
            "estado_skipped": 0,
        }
        missing_comedores: List[Dict[str, object]] = []
        error_details: List[str] = []

        for line_number, row in self._iter_rows(csv_path, delimiter, encoding):
            stats["rows"] += 1
            try:
                comedor_id = self._parse_int_field(
                    row.get("comedor_id"), "comedor_id", line_number, required=True
                )
            except ValueError as error:
                stats["errors"] += 1
                message = str(error)
                error_details.append(message)
                self.stdout.write(self.style.ERROR(message))
                continue

            try:
                comedor = Comedor.objects.select_related(
                    "ultimo_estado", "ultimo_estado__estado_general"
                ).get(pk=comedor_id)
            except Comedor.DoesNotExist:
                stats["errors"] += 1
                missing_comedores.append(
                    {"linea": line_number, "comedor_id": comedor_id}
                )
                message = (
                    f"Línea {line_number}: no existe un comedor con id {comedor_id}."
                )
                error_details.append(message)
                self.stdout.write(self.style.ERROR(message))
                continue

            programa_needs_update = comedor.programa_id != programa.id
            estado_needs_update = not self._matches_estado_actual(
                comedor, actividad, proceso, detalle
            )

            description = (
                f"Línea {line_number}: comedor {comedor.id} ({comedor.nombre})"
            )

            if dry_run:
                cambios = []
                if programa_needs_update:
                    cambios.append("programa")
                if estado_needs_update:
                    cambios.append("estado")
                cambios_txt = ", ".join(cambios) if cambios else "sin cambios"
                self.stdout.write(f"[DRY-RUN] {description} -> {cambios_txt}")
                self._update_stats(
                    stats, programa_needs_update, estado_needs_update, applied=bool(cambios)
                )
                continue

            if not (programa_needs_update or estado_needs_update):
                stats["skipped"] += 1
                stats["programa_skipped"] += 1
                stats["estado_skipped"] += 1
                self.stdout.write(self.style.WARNING(f"{description} (sin cambios)"))
                continue

            previous_historial_id = getattr(
                getattr(comedor, "ultimo_estado", None), "id", None
            )

            with transaction.atomic():
                if programa_needs_update:
                    comedor.programa = programa
                    comedor.save(update_fields=["programa"])

                historial = None
                if estado_needs_update:
                    historial = registrar_cambio_estado(
                        comedor=comedor,
                        actividad=actividad,
                        proceso=proceso,
                        detalle=detalle,
                    )

            estado_changed = (
                estado_needs_update
                and getattr(historial, "id", None) != previous_historial_id
            )

            self._update_stats(
                stats,
                programa_needs_update,
                estado_changed,
                applied=programa_needs_update or estado_changed,
            )
            self.stdout.write(self.style.SUCCESS(description))

        self._print_summary(stats, missing_comedores, error_details, dry_run)

    def _iter_rows(
        self, csv_path: Path, delimiter: str, encoding: str
    ) -> Iterable[Tuple[int, Dict[str, Optional[str]]]]:
        with csv_path.open("r", encoding=encoding, newline="") as csv_file:
            reader = csv.DictReader(csv_file, delimiter=delimiter)
            if reader.fieldnames is None:
                raise CommandError("El CSV debe incluir encabezados.")

            normalized_headers = [self._normalize_header(h) for h in reader.fieldnames]
            reader.fieldnames = normalized_headers
            self._validate_headers(set(normalized_headers))

            for line_number, raw_row in enumerate(reader, start=2):
                row = {
                    key: (value.strip() if isinstance(value, str) else value)
                    for key, value in raw_row.items()
                }
                if not any((value or "").strip() for value in row.values()):
                    continue
                yield line_number, row

    def _normalize_header(self, header: Optional[str]) -> str:
        normalized = (header or "").lstrip("\ufeff").strip().lower().replace(" ", "_")
        return HEADER_ALIASES.get(normalized, normalized)

    def _validate_headers(self, headers: set) -> None:
        missing = REQUIRED_HEADERS - headers
        if missing:
            raise CommandError(
                "Falta la columna obligatoria: " + ", ".join(sorted(missing))
            )

    def _parse_int_field(
        self,
        raw_value: Optional[str],
        field_name: str,
        line_number: int,
        required: bool = False,
    ) -> Optional[int]:
        if raw_value is None or str(raw_value).strip() == "":
            if required:
                raise ValueError(
                    f"Línea {line_number}: el campo '{field_name}' está vacío."
                )
            return None

        text = str(raw_value).strip()
        try:
            number = Decimal(text)
        except (TypeError, InvalidOperation):
            raise ValueError(
                f"Línea {line_number}: no se pudo convertir '{raw_value}' a entero "
                f"para el campo '{field_name}'."
            )
        if not number.is_finite() or number != number.to_integral_value():
            raise ValueError(
                f"Línea {line_number}: '{raw_value}' no es un entero válido "
                f"para el campo '{field_name}'."
            )
        return int(number)

    def _resolve_programa(self, programa_id: int) -> Programas:
        try:
            return Programas.objects.get(pk=programa_id)
        except Programas.DoesNotExist:
            raise CommandError(
                f"No existe un programa con id {programa_id}."
            ) from None

    def _resolve_estado_actividad(self, label: str) -> EstadoActividad:
        queryset = EstadoActividad.objects.filter(estado__iexact=label)
        count = queryset.count()
        if count == 1:
            return queryset.first()
        if count > 1:
            raise CommandError(f"Hay {count} EstadoActividad con el nombre '{label}'.")

        normalized_label = self._normalize_text(label)
        candidates = list(EstadoActividad.objects.all())
        matches = [
            candidate
            for candidate in candidates
            if self._normalize_text(candidate.estado) == normalized_label
        ]
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            raise CommandError(
                f"Hay {len(matches)} EstadoActividad equivalentes a '{label}'."
            )
        raise CommandError(f"No existe EstadoActividad '{label}'.")

    def _resolve_estado_proceso(
        self, actividad: EstadoActividad, label: str
    ) -> EstadoProceso:
        queryset = EstadoProceso.objects.filter(
            estado__iexact=label, estado_actividad=actividad
        )
        count = queryset.count()
        if count == 1:
            return queryset.first()
        if count > 1:
            raise CommandError(
                f"Hay {count} EstadoProceso llamados '{label}' para '{actividad.estado}'."
            )

        normalized_label = self._normalize_text(label)
        candidates = list(EstadoProceso.objects.filter(estado_actividad=actividad))
        matches = [
            candidate
            for candidate in candidates
            if self._normalize_text(candidate.estado) == normalized_label
        ]
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            raise CommandError(
                f"Hay {len(matches)} EstadoProceso equivalentes a '{label}' para "
                f"'{actividad.estado}'."
            )
        raise CommandError(
            f"No existe EstadoProceso '{label}' para '{actividad.estado}'."
        )

    def _resolve_estado_detalle(
        self, proceso: EstadoProceso, label: str
    ) -> EstadoDetalle:
        queryset = EstadoDetalle.objects.filter(
            estado__iexact=label, estado_proceso=proceso
        )
        count = queryset.count()
        if count == 1:
            return queryset.first()
        if count > 1:
            raise CommandError(
                f"Hay {count} EstadoDetalle llamados '{label}' para '{proceso.estado}'."
            )

        normalized_label = self._normalize_text(label)
        candidates = list(EstadoDetalle.objects.filter(estado_proceso=proceso))
        matches = [
            candidate
            for candidate in candidates
            if self._normalize_text(candidate.estado) == normalized_label
        ]
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            raise CommandError(
                f"Hay {len(matches)} EstadoDetalle equivalentes a '{label}' para "
                f"'{proceso.estado}'."
            )
        raise CommandError(
            f"No existe EstadoDetalle '{label}' para '{proceso.estado}'."
        )

    def _normalize_text(self, value: str) -> str:
        normalized = unicodedata.normalize("NFKD", value)
        normalized = "".join(ch for ch in normalized if not unicodedata.combining(ch))
        return normalized.casefold()

    def _matches_estado_actual(
        self,
        comedor: Comedor,
        actividad: EstadoActividad,
        proceso: EstadoProceso,
        detalle: Optional[EstadoDetalle],
    ) -> bool:
        ultimo = getattr(comedor, "ultimo_estado", None)
        if not ultimo or not ultimo.estado_general_id:
            return False
        estado_general = ultimo.estado_general
        detalle_id = detalle.id if detalle else None
        return (
            estado_general.estado_actividad_id == actividad.id
            and estado_general.estado_proceso_id == proceso.id
            and estado_general.estado_detalle_id == detalle_id
        )

    def _update_stats(
        self,
        stats: Dict[str, int],
        programa_changed: bool,
        estado_changed: bool,
        applied: bool,
    ) -> None:
        if applied:
            stats["applied"] += 1
        elif not (programa_changed or estado_changed):
            stats["skipped"] += 1
        if programa_changed:
            stats["programa_updates"] += 1
        else:
            stats["programa_skipped"] += 1
        if estado_changed:
            stats["estado_updates"] += 1
        else:
            stats["estado_skipped"] += 1

    def _print_summary(
        self,
        stats: Dict[str, int],
        missing_comedores: List[Dict[str, object]],
        error_details: List[str],
        dry_run: bool,
    ) -> None:
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=== Resumen ==="))
        self.stdout.write(f"Filas procesadas: {stats['rows']}")
        self.stdout.write(f"Filas con cambios: {stats['applied']}")
        self.stdout.write(f"Programas actualizados: {stats['programa_updates']}")
        self.stdout.write(f"Estados actualizados: {stats['estado_updates']}")
        self.stdout.write(f"Filas sin cambios: {stats['skipped']}")
        self.stdout.write(f"Filas con errores: {stats['errors']}")

        if missing_comedores:
            self.stdout.write("")
            self.stdout.write(self.style.WARNING("Comedores no encontrados:"))
            for item in missing_comedores:
                self.stdout.write(
                    f"  Línea {item.get('linea')}: comedor_id={item.get('comedor_id')}"
                )

        if error_details:
            self.stdout.write("")
            self.stdout.write("Detalle de errores:")
            for detail in error_details:
                self.stdout.write(f"  - {detail}")

        if dry_run:
            self.stdout.write("")
            self.stdout.write("Modo dry-run: no se aplicaron cambios.")
