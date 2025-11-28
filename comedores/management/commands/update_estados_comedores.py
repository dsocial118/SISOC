import csv
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from comedores.models import (
    Comedor,
    EstadoActividad,
    EstadoDetalle,
    EstadoProceso,
)
from comedores.services.estado_manager import registrar_cambio_estado

HEADER_ALIASES = {
    "comedor__nombre": "nombre",
    "comedor_nombre": "nombre",
    "nombre": "nombre",
    "comedor": "nombre",
    "sisoc_id": "sisoc_id",
    "id": "sisoc_id",
    "estado_actividad": "estado_actividad",
    "estadoactividad": "estado_actividad",
    "estado_proceso": "estado_proceso",
    "estadoproceso": "estado_proceso",
    "estado_detalle": "estado_detalle",
    "estadodetalle": "estado_detalle",
}
REQUIRED_STATE_FIELDS = {"estado_actividad"}


class Command(BaseCommand):
    """
    Actualiza el historial de estado de los comedores a partir de un CSV.

    El archivo debe incluir las columnas `estado_actividad`, `estado_proceso`,
    `estado_detalle` y un identificador del comedor (`sisoc_id` o `comedor__nombre`).
    """

    help = (
        "Crea registros de EstadoHistorial leyendo un CSV con "
        "sisoc_id/comedor__nombre, estado_actividad, estado_proceso y estado_detalle."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "csv_path",
            help="Ruta del archivo CSV con los estados a aplicar.",
        )
        parser.add_argument(
            "--delimiter",
            default=",",
            help="Separador de columnas del CSV. Por defecto ','.",
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
        dry_run = options["dry_run"]

        if not csv_path.exists():
            raise CommandError(f"El archivo '{csv_path}' no existe.")
        if not csv_path.is_file():
            raise CommandError(f"'{csv_path}' no es un archivo válido.")

        stats = {"rows": 0, "applied": 0, "skipped": 0, "errors": 0}
        missing_comedores: List[Dict[str, object]] = []
        error_details: List[str] = []

        for line_number, row in self._iter_rows(csv_path, delimiter):
            stats["rows"] += 1
            try:
                comedor = self._resolve_comedor(row, line_number, missing_comedores)
                actividad, proceso, detalle = self._resolve_estados(row, line_number)
            except ValueError as error:
                stats["errors"] += 1
                message = str(error)
                error_details.append(message)
                self.stdout.write(self.style.ERROR(message))
                continue

            description = (
                f"Línea {line_number}: comedor {comedor.pk} ({comedor.nombre}) -> "
                f"actividad={actividad.id}"
            )
            if proceso:
                description += f", proceso={proceso.id}"
            if detalle:
                description += f", detalle={detalle.id}"

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
        self, csv_path: Path, delimiter: str
    ) -> Iterable[Tuple[int, Dict[str, Optional[str]]]]:
        with csv_path.open("r", encoding="utf-8", newline="") as csv_file:
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
        normalized = (header or "").strip().lower()
        return HEADER_ALIASES.get(normalized, normalized)

    def _validate_headers(self, headers: set) -> None:
        if not ({"sisoc_id", "nombre"} & headers):
            raise CommandError(
                "El CSV debe contener alguna columna para identificar el comedor: "
                "'sisoc_id' o 'comedor__nombre'."
            )
        missing_states = REQUIRED_STATE_FIELDS - headers
        if missing_states:
            raise CommandError(
                "Faltan columnas obligatorias: " + ", ".join(sorted(missing_states))
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
        sisoc_raw = row.get("sisoc_id")
        nombre_raw = row.get("nombre")

        if sisoc_raw is not None and str(sisoc_raw).strip() != "":
            comedor_id = self._parse_int_field(
                sisoc_raw, "sisoc_id", line_number, required=True
            )
            try:
                return Comedor.objects.get(pk=comedor_id)
            except Comedor.DoesNotExist:
                missing_comedores.append(
                    {
                        "linea": line_number,
                        "sisoc_id": comedor_id,
                        "nombre": nombre_raw or "",
                    }
                )
                raise ValueError(
                    f"Línea {line_number}: no existe un comedor con id {comedor_id}."
                ) from None

        if nombre_raw:
            nombre = str(nombre_raw).strip()
            if nombre:
                queryset = Comedor.objects.filter(nombre__iexact=nombre)
                count = queryset.count()
                if count == 0:
                    missing_comedores.append(
                        {
                            "linea": line_number,
                            "sisoc_id": sisoc_raw or "",
                            "nombre": nombre,
                        }
                    )
                    raise ValueError(
                        f"Línea {line_number}: no existe un comedor con nombre '{nombre}'."
                    )
                if count > 1:
                    raise ValueError(
                        f"Línea {line_number}: hay {count} comedores con el nombre "
                        f"'{nombre}', especifique 'sisoc_id' para desambiguar."
                    )
                return queryset.first()

        raise ValueError(
            f"Línea {line_number}: no se proporcionó 'sisoc_id' ni 'comedor__nombre'."
        )

    def _resolve_estados(
        self, row: Dict[str, Optional[str]], line_number: int
    ) -> Tuple[EstadoActividad, Optional[EstadoProceso], Optional[EstadoDetalle]]:
        actividad_id = self._parse_int_field(
            row.get("estado_actividad"),
            "estado_actividad",
            line_number,
            required=True,
        )
        proceso_id = self._parse_int_field(
            row.get("estado_proceso"), "estado_proceso", line_number, required=False
        )
        detalle_id = self._parse_int_field(
            row.get("estado_detalle"), "estado_detalle", line_number, required=False
        )

        try:
            actividad = EstadoActividad.objects.get(pk=actividad_id)
        except EstadoActividad.DoesNotExist:
            raise ValueError(
                f"Línea {line_number}: no existe EstadoActividad con id {actividad_id}."
            ) from None

        proceso = None
        if proceso_id is not None:
            try:
                proceso = EstadoProceso.objects.get(pk=proceso_id)
            except EstadoProceso.DoesNotExist:
                raise ValueError(
                    f"Línea {line_number}: no existe EstadoProceso con id {proceso_id}."
                ) from None
            if proceso.estado_actividad_id != actividad.id:
                raise ValueError(
                    f"Línea {line_number}: el EstadoProceso {proceso_id} no pertenece "
                    f"al EstadoActividad {actividad.id}."
                )

        detalle = None
        if detalle_id is not None:
            try:
                detalle = EstadoDetalle.objects.get(pk=detalle_id)
            except EstadoDetalle.DoesNotExist:
                raise ValueError(
                    f"Línea {line_number}: no existe EstadoDetalle con id {detalle_id}."
                ) from None
            if proceso and detalle.estado_proceso_id != proceso.id:
                raise ValueError(
                    f"Línea {line_number}: el EstadoDetalle {detalle_id} no pertenece "
                    f"al EstadoProceso {proceso_id}."
                )
            proceso = proceso or detalle.estado_proceso
            if proceso.estado_actividad_id != actividad.id:
                raise ValueError(
                    f"Línea {line_number}: el EstadoDetalle {detalle_id} no pertenece "
                    f"al EstadoActividad {actividad.id}."
                )

        return actividad, proceso, detalle

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
                nombre = item.get("nombre") or "(sin nombre)"
                sisoc_id = item.get("sisoc_id")
                sisoc_part = f", sisoc_id={sisoc_id}" if sisoc_id else ""
                self.stdout.write(
                    f"  Línea {item.get('linea')}: nombre='{nombre}'{sisoc_part}"
                )

        if error_details:
            self.stdout.write("")
            self.stdout.write("Detalle de errores:")
            for detail in error_details:
                self.stdout.write(f"  - {detail}")

        if dry_run:
            self.stdout.write("")
            self.stdout.write("Modo dry-run: no se aplicaron cambios en la base.")
