import csv
from pathlib import Path
from typing import Iterator, Tuple

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from comedores.models import Comedor
from duplas.models import Dupla


class Command(BaseCommand):
    """
    Actualiza el campo `dupla` del modelo Comedor a partir de un CSV que
    contenga las columnas `dupla_id` y `comedor_id`.
    """

    help = "Asignar duplas a comedores leyendo un archivo CSV."
    required_columns = {"dupla_id", "comedor_id"}

    def add_arguments(self, parser):
        parser.add_argument(
            "csv_path",
            help="Ruta del archivo CSV con las columnas 'dupla_id' y 'comedor_id'.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            dest="dry_run",
            help="Muestra los cambios sin persistirlos en la base de datos.",
        )

    def handle(self, *args, **options):
        csv_path = Path(options["csv_path"]).expanduser()
        dry_run = options["dry_run"]

        if not csv_path.exists():
            raise CommandError(f"El archivo '{csv_path}' no existe.")
        if not csv_path.is_file():
            raise CommandError(f"'{csv_path}' no es un archivo válido.")

        stats = {
            "rows": 0,
            "updates": 0,
            "applied": 0,
            "skipped": 0,
            "errors": 0,
            "skipped_lines": [],
            "error_lines": [],
        }

        for line_number, row in self._iter_rows(csv_path):
            stats["rows"] += 1

            try:
                dupla_id = self._parse_int(row.get("dupla_id"), "dupla_id", line_number)
                comedor_id = self._parse_int(
                    row.get("comedor_id"), "comedor_id", line_number
                )
            except ValueError as error:
                stats["errors"] += 1
                stats["error_lines"].append(line_number)
                self.stdout.write(self.style.ERROR(str(error)))
                continue

            try:
                comedor = Comedor.objects.select_related("dupla").get(pk=comedor_id)
            except Comedor.DoesNotExist:
                stats["errors"] += 1
                stats["error_lines"].append(line_number)
                self.stdout.write(
                    self.style.ERROR(
                        f"Línea {line_number}: el comedor {comedor_id} no existe."
                    )
                )
                continue

            try:
                dupla = Dupla.objects.get(pk=dupla_id)
            except Dupla.DoesNotExist:
                stats["errors"] += 1
                stats["error_lines"].append(line_number)
                self.stdout.write(
                    self.style.ERROR(
                        f"Línea {line_number}: la dupla {dupla_id} no existe."
                    )
                )
                continue

            previous_dupla_id = comedor.dupla_id
            previous_dupla_label = (
                f"{previous_dupla_id}" if previous_dupla_id else "sin dupla"
            )

            if previous_dupla_id == dupla.id:
                stats["skipped"] += 1
                stats["skipped_lines"].append(line_number)
                self.stdout.write(
                    self.style.WARNING(
                        f"Línea {line_number}: comedor {comedor_id} ya tiene la "
                        f"dupla {dupla_id}, se omite."
                    )
                )
                continue

            stats["updates"] += 1
            change_message = (
                f"Comedor {comedor.id} ({comedor.nombre}): {previous_dupla_label} -> {dupla.id}"
            )

            if dry_run:
                self.stdout.write(f"[DRY-RUN] {change_message}")
                continue

            with transaction.atomic():
                comedor.dupla = dupla
                comedor.save(update_fields=["dupla"])

            stats["applied"] += 1
            self.stdout.write(self.style.SUCCESS(f"[APLICADO] {change_message}"))

        self._print_summary(stats, dry_run)

    def _iter_rows(self, csv_path: Path) -> Iterator[Tuple[int, dict]]:
        with csv_path.open("r", encoding="utf-8", newline="") as csv_file:
            reader = csv.DictReader(csv_file)
            if reader.fieldnames is None:
                raise CommandError("El CSV debe incluir encabezados.")

            normalized_headers = [
                (header or "").strip().lower() for header in reader.fieldnames
            ]
            reader.fieldnames = normalized_headers

            missing = self.required_columns - set(normalized_headers)
            if missing:
                raise CommandError(
                    "El CSV debe contener las columnas: "
                    + ", ".join(sorted(self.required_columns))
                )

            for line_number, row in enumerate(reader, start=2):
                if not any((value or "").strip() for value in row.values()):
                    continue
                yield line_number, row

    def _parse_int(self, raw_value, field_name: str, line_number: int) -> int:
        if raw_value is None or str(raw_value).strip() == "":
            raise ValueError(
                f"Línea {line_number}: el campo '{field_name}' está vacío."
            )
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

    def _print_summary(self, stats: dict, dry_run: bool) -> None:
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=== Resumen ==="))
        self.stdout.write(f"Filas procesadas: {stats['rows']}")
        self.stdout.write(f"Actualizaciones detectadas: {stats['updates']}")
        self.stdout.write(f"Filas sin cambios: {stats['skipped']}")
        if stats["skipped_lines"]:
            self.stdout.write(
                f"  Líneas omitidas: {', '.join(map(str, stats['skipped_lines']))}"
            )
        self.stdout.write(f"Filas con errores: {stats['errors']}")
        if stats["error_lines"]:
            self.stdout.write(
                f"  Líneas con errores: {', '.join(map(str, stats['error_lines']))}"
            )
        if dry_run:
            self.stdout.write("Modo dry-run: no se aplicaron cambios.")
        else:
            self.stdout.write(f"Actualizaciones aplicadas: {stats['applied']}")
