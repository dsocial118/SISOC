import csv
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from comedores.models import Comedor, EstadoActividad, EstadoDetalle, EstadoProceso
from comedores.services.estado_manager import registrar_cambio_estado

HEADER_ALIASES = {
    "estado_general": "estado_actividad",
    "estadogeneral": "estado_actividad",
    "estado general": "estado_actividad",
    "estado": "estado_actividad",
    "subestado": "estado_proceso",
    "estado_proceso": "estado_proceso",
    "estadoproceso": "estado_proceso",
    "motivo": "estado_detalle",
    "estado_detalle": "estado_detalle",
    "estadodetalle": "estado_detalle",
    "detalle": "estado_detalle",
    "comedor_id": "comedor_id",
    "comedor": "comedor_id",
    "id": "comedor_id",
}
REQUIRED_HEADERS = {"estado_actividad", "estado_proceso", "comedor_id"}


class Command(BaseCommand):
    """
    Actualiza el historial de estados de los comedores a partir de un CSV con nombres.

    El CSV debe incluir las columnas `Estado General`, `Subestado`, `Motivo` y
    `comedor_id`. Los valores de estado se buscan por su nombre (case-insensitive).
    """

    help = (
        "Crea registros de EstadoHistorial leyendo un CSV con comedor_id, "
        "Estado General, Subestado y Motivo (usando los nombres de las opciones)."
    )

    def add_arguments(self, parser):
        parser.add_argument("csv_path", help="Ruta del archivo CSV con los estados.")
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
            help="Muestra los cambios sin guardarlos en la base de datos.",
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

        # Caches para evitar consultas repetidas
        self._actividad_cache: Dict[str, EstadoActividad] = {}
        self._proceso_cache: Dict[Tuple[int, str], EstadoProceso] = {}
        self._detalle_cache: Dict[Tuple[int, str], EstadoDetalle] = {}

        stats = {"rows": 0, "applied": 0, "skipped": 0, "errors": 0}
        missing_comedores: List[Dict[str, object]] = []
        error_details: List[str] = []

        for line_number, row in self._iter_rows(csv_path, delimiter, encoding):
            stats["rows"] += 1
            try:
                comedor = self._resolve_comedor(row, line_number, missing_comedores)
                actividad = self._resolve_estado_actividad(row, line_number)
                proceso = self._resolve_estado_proceso(row, line_number, actividad)
                detalle = self._resolve_estado_detalle(
                    row, line_number, proceso, actividad
                )
            except ValueError as error:
                stats["errors"] += 1
                message = str(error)
                error_details.append(message)
                self.stdout.write(self.style.ERROR(message))
                continue

            description = (
                f"Línea {line_number}: comedor {comedor.pk} ({comedor.nombre}) -> "
                f"estado='{actividad.estado}', subestado='{proceso.estado}'"
            )
            if detalle:
                description += f", motivo='{detalle.estado}'"

            if dry_run:
                self.stdout.write(f"[DRY-RUN] {description}")
                continue

            previous_historial_id = getattr(
                getattr(comedor, "ultimo_estado", None), "id", None
            )
            with transaction.atomic():
                historial = registrar_cambio_estado(
                    comedor=comedor,
                    actividad=actividad,
                    proceso=proceso,
                    detalle=detalle,
                )

            if getattr(historial, "id", None) == previous_historial_id:
                stats["skipped"] += 1
                self.stdout.write(
                    self.style.WARNING(
                        f"{description} (sin cambios: ya tenía este estado)"
                    )
                )
            else:
                stats["applied"] += 1
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
        normalized = (header or "").strip().lower().replace(" ", "_")
        return HEADER_ALIASES.get(normalized, normalized)

    def _validate_headers(self, headers: set) -> None:
        missing = REQUIRED_HEADERS - headers
        if missing:
            raise CommandError(
                "Faltan columnas obligatorias: " + ", ".join(sorted(missing))
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

    def _resolve_comedor(
        self,
        row: Dict[str, Optional[str]],
        line_number: int,
        missing_comedores: List[Dict[str, object]],
    ) -> Comedor:
        raw_id = row.get("comedor_id")
        comedor_id = self._parse_int_field(raw_id, "comedor_id", line_number, True)
        try:
            return Comedor.objects.get(pk=comedor_id)
        except Comedor.DoesNotExist:
            missing_comedores.append({"linea": line_number, "comedor_id": comedor_id})
            raise ValueError(
                f"Línea {line_number}: no existe un comedor con id {comedor_id}."
            ) from None

    def _resolve_estado_actividad(
        self, row: Dict[str, Optional[str]], line_number: int
    ) -> EstadoActividad:
        raw_value = row.get("estado_actividad")
        if raw_value is None or not str(raw_value).strip():
            raise ValueError(
                f"Línea {line_number}: el campo 'Estado General' está vacío."
            )

        key = str(raw_value).strip().casefold()
        if key in self._actividad_cache:
            return self._actividad_cache[key]

        queryset = EstadoActividad.objects.filter(estado__iexact=raw_value.strip())
        count = queryset.count()
        if count == 0:
            raise ValueError(
                f"Línea {line_number}: no existe Estado General '{raw_value}'."
            )
        if count > 1:
            raise ValueError(
                f"Línea {line_number}: hay {count} Estados Generales con el nombre "
                f"'{raw_value}'."
            )

        actividad = queryset.first()
        self._actividad_cache[key] = actividad
        return actividad

    def _resolve_estado_proceso(
        self,
        row: Dict[str, Optional[str]],
        line_number: int,
        actividad: EstadoActividad,
    ) -> EstadoProceso:
        raw_value = row.get("estado_proceso")
        if raw_value is None or not str(raw_value).strip():
            raise ValueError(f"Línea {line_number}: el campo 'Subestado' está vacío.")

        key = (actividad.id, str(raw_value).strip().casefold())
        if key in self._proceso_cache:
            return self._proceso_cache[key]

        base_queryset = EstadoProceso.objects.filter(
            estado__iexact=raw_value.strip(), estado_actividad=actividad
        )
        count = base_queryset.count()
        if count == 0:
            exists_elsewhere = EstadoProceso.objects.filter(
                estado__iexact=raw_value.strip()
            ).exists()
            if exists_elsewhere:
                raise ValueError(
                    f"Línea {line_number}: el Subestado '{raw_value}' no pertenece "
                    f"al Estado General '{actividad.estado}'."
                )
            raise ValueError(f"Línea {line_number}: no existe Subestado '{raw_value}'.")
        if count > 1:
            raise ValueError(
                f"Línea {line_number}: hay {count} Subestados llamados "
                f"'{raw_value}' para el Estado General '{actividad.estado}'."
            )

        proceso = base_queryset.first()
        self._proceso_cache[key] = proceso
        return proceso

    def _resolve_estado_detalle(
        self,
        row: Dict[str, Optional[str]],
        line_number: int,
        proceso: EstadoProceso,
        actividad: EstadoActividad,
    ) -> Optional[EstadoDetalle]:
        raw_value = row.get("estado_detalle")
        if raw_value is None or str(raw_value).strip() == "":
            return None

        key = (proceso.id, str(raw_value).strip().casefold())
        if key in self._detalle_cache:
            return self._detalle_cache[key]

        base_queryset = EstadoDetalle.objects.filter(
            estado__iexact=raw_value.strip(), estado_proceso=proceso
        )
        count = base_queryset.count()
        if count == 0:
            exists_elsewhere = EstadoDetalle.objects.filter(
                estado__iexact=raw_value.strip()
            ).exists()
            if exists_elsewhere:
                raise ValueError(
                    f"Línea {line_number}: el Motivo '{raw_value}' no pertenece al "
                    f"Subestado '{proceso.estado}' del Estado General "
                    f"'{actividad.estado}'."
                )
            raise ValueError(f"Línea {line_number}: no existe Motivo '{raw_value}'.")
        if count > 1:
            raise ValueError(
                f"Línea {line_number}: hay {count} Motivos llamados '{raw_value}' "
                f"para el Subestado '{proceso.estado}'."
            )

        detalle = base_queryset.first()
        self._detalle_cache[key] = detalle
        return detalle

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
        self.stdout.write(f"Actualizaciones aplicadas: {stats['applied']}")
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
            self.stdout.write("Modo dry-run: no se aplicaron cambios en la base.")
