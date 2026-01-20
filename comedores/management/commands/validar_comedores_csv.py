import csv
import unicodedata
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from comedores.models import (
    Comedor,
    EstadoActividad,
    EstadoProceso,
    HistorialValidacion,
)
from comedores.services.estado_manager import registrar_cambio_estado

VALIDACION_ESTADO = "Validado"
ESTADO_ACTIVIDAD_LABEL = "Activo"
ESTADO_PROCESO_LABEL = "En ejecución"

HEADER_ALIASES = {
    "comedor_id": "comedor_id",
    "comedor": "comedor_id",
    "id": "comedor_id",
}
REQUIRED_HEADERS = {"comedor_id"}


class Command(BaseCommand):
    """
    Valida comedores desde un CSV con la columna `comedor_id` y deja el estado
    general en Activo / En ejecución.
    """

    help = (
        "Actualiza estado_validacion=Validado y ultimo_estado=Activo/En ejecución "
        "para comedores listados en un CSV."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "csv_path",
            help="Ruta del archivo CSV con la columna 'comedor_id'.",
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

        actividad = self._resolve_estado_actividad(
            ESTADO_ACTIVIDAD_LABEL, create_missing=not dry_run
        )
        proceso = self._resolve_estado_proceso(
            actividad, ESTADO_PROCESO_LABEL, create_missing=not dry_run
        )

        stats = {
            "rows": 0,
            "applied": 0,
            "skipped": 0,
            "errors": 0,
            "validacion_updates": 0,
            "validacion_skipped": 0,
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

            validacion_needs_update = (
                comedor.estado_validacion != VALIDACION_ESTADO
                or comedor.fecha_validado is None
            )
            estado_needs_update = not self._matches_estado_actual(
                comedor, actividad, proceso
            )

            description = f"Línea {line_number}: comedor {comedor.id} ({comedor.nombre})"

            if dry_run:
                cambios = []
                if validacion_needs_update:
                    cambios.append("validación")
                if estado_needs_update:
                    cambios.append("estado")
                cambios_txt = ", ".join(cambios) if cambios else "sin cambios"
                self.stdout.write(f"[DRY-RUN] {description} -> {cambios_txt}")
                self._update_stats(
                    stats,
                    validacion_needs_update,
                    estado_needs_update,
                    applied=validacion_needs_update or estado_needs_update,
                )
                continue

            previous_historial_id = getattr(
                getattr(comedor, "ultimo_estado", None), "id", None
            )

            with transaction.atomic():
                if validacion_needs_update:
                    comedor.estado_validacion = VALIDACION_ESTADO
                    comedor.fecha_validado = timezone.now()
                    comedor.save(update_fields=["estado_validacion", "fecha_validado"])
                    HistorialValidacion.objects.create(
                        comedor=comedor,
                        usuario=None,
                        estado_validacion=VALIDACION_ESTADO,
                    )

                historial = registrar_cambio_estado(
                    comedor=comedor,
                    actividad=actividad,
                    proceso=proceso,
                    detalle=None,
                )

            estado_changed = getattr(historial, "id", None) != previous_historial_id

            applied = validacion_needs_update or estado_changed
            if applied:
                self.stdout.write(self.style.SUCCESS(description))
            else:
                self.stdout.write(
                    self.style.WARNING(f"{description} (sin cambios)")
                )

            self._update_stats(
                stats, validacion_needs_update, estado_changed, applied=applied
            )

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
        normalized = (header or "").strip().lower().replace(" ", "_")
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
            if "." in text:
                return int(float(text))
            return int(text)
        except (TypeError, ValueError):
            raise ValueError(
                f"Línea {line_number}: no se pudo convertir '{raw_value}' a entero "
                f"para el campo '{field_name}'."
            )

    def _resolve_estado_actividad(
        self, label: str, create_missing: bool
    ) -> EstadoActividad:
        queryset = EstadoActividad.objects.filter(estado__iexact=label)
        count = queryset.count()
        if count == 1:
            return queryset.first()
        if count > 1:
            raise CommandError(
                f"Hay {count} EstadoActividad con el nombre '{label}'."
            )
        if not create_missing:
            raise CommandError(
                f"No existe EstadoActividad '{label}'. Ejecutá sin --dry-run para crearlo."
            )
        return EstadoActividad.objects.create(estado=label)

    def _resolve_estado_proceso(
        self, actividad: EstadoActividad, label: str, create_missing: bool
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
        if not create_missing:
            raise CommandError(
                f"No existe EstadoProceso '{label}' para '{actividad.estado}'. "
                "Ejecutá sin --dry-run para crearlo."
            )
        return EstadoProceso.objects.create(estado=label, estado_actividad=actividad)

    def _normalize_text(self, value: str) -> str:
        normalized = unicodedata.normalize("NFKD", value)
        normalized = "".join(
            ch for ch in normalized if not unicodedata.combining(ch)
        )
        return normalized.casefold()

    def _matches_estado_actual(
        self, comedor: Comedor, actividad: EstadoActividad, proceso: EstadoProceso
    ) -> bool:
        ultimo = getattr(comedor, "ultimo_estado", None)
        if not ultimo or not ultimo.estado_general_id:
            return False
        estado_general = ultimo.estado_general
        return (
            estado_general.estado_actividad_id == actividad.id
            and estado_general.estado_proceso_id == proceso.id
            and estado_general.estado_detalle_id is None
        )

    def _update_stats(
        self,
        stats: Dict[str, int],
        validacion_changed: bool,
        estado_changed: bool,
        applied: bool,
    ) -> None:
        if applied:
            stats["applied"] += 1
        elif not (validacion_changed or estado_changed):
            stats["skipped"] += 1
        if validacion_changed:
            stats["validacion_updates"] += 1
        else:
            stats["validacion_skipped"] += 1
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
        self.stdout.write(f"Validaciones actualizadas: {stats['validacion_updates']}")
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
