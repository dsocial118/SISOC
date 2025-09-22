"""Comando para eliminar relevamientos específicos respetando signals."""

import math
import re
import time
from typing import Iterable, List

from django.core.management.base import BaseCommand, CommandError

from relevamientos.models import Relevamiento


class Command(BaseCommand):
    help = (
        "Elimina Relevamientos por ID en lotes pequeños, ejecutando las signals "
        "habituales (pre_delete) para sincronizaciones externas."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "ids",
            nargs="*",
            help="IDs de Relevamiento a eliminar. Se aceptan múltiples valores",
        )
        parser.add_argument(
            "--from-file",
            dest="ids_file",
            help=(
                "Ruta a un archivo con IDs (separados por coma, espacio o salto de "
                "línea)."
            ),
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=10,
            help="Cantidad de IDs a eliminar por lote. Default: 10.",
        )
        parser.add_argument(
            "--sleep",
            type=float,
            default=0.0,
            help="Segundos de espera entre lotes para evitar timeouts.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Muestra qué IDs se eliminarían sin ejecutar cambios.",
        )
        parser.add_argument(
            "--ignore-missing",
            action="store_true",
            help="No falla si algún ID no existe.",
        )

    def handle(self, *args, **options):
        ids = self._collect_ids(options)
        if not ids:
            raise CommandError(
                "Debe indicar al menos un ID por argumento o mediante --from-file."
            )

        batch_size = options["batch_size"]
        sleep_seconds = options["sleep"]
        dry_run = options["dry_run"]
        ignore_missing = options["ignore_missing"]

        if batch_size <= 0:
            raise CommandError("--batch-size debe ser mayor que cero.")
        if sleep_seconds < 0:
            raise CommandError("--sleep no puede ser negativo.")

        total = len(ids)
        total_batches = math.ceil(total / batch_size)
        deleted = 0
        missing: List[int] = []

        for batch_index, batch_ids in enumerate(self._chunk(ids, batch_size), start=1):
            self.stdout.write(f"Procesando lote {batch_index}/{total_batches}: {batch_ids}")

            qs = Relevamiento.objects.filter(id__in=batch_ids)
            found = {obj.id: obj for obj in qs}

            for pk in batch_ids:
                obj = found.get(pk)
                if not obj:
                    missing.append(pk)
                    self.stderr.write(f"Relevamiento con id={pk} no existe.")
                    continue

                if dry_run:
                    self.stdout.write(f"[dry-run] Se eliminaría relevamiento {pk}.")
                    continue

                obj.delete()  # Dispara signals pre_delete y post_delete habituales
                deleted += 1
                self.stdout.write(self.style.SUCCESS(f"Eliminado relevamiento {pk}."))

            if sleep_seconds > 0 and not dry_run and batch_index < total_batches:
                time.sleep(sleep_seconds)

        if missing and not ignore_missing:
            unique_missing = ", ".join(str(pk) for pk in sorted(set(missing)))
            raise CommandError(
                f"Finalizó con faltantes. No se encontraron relevamientos con ids: {unique_missing}"
            )

        self.stdout.write(
            self.style.SUCCESS(
                "Proceso finalizado. "
                f"IDs solicitados: {total}. "
                f"Eliminados: {deleted if not dry_run else 0}. "
                f"Omitidos (no existentes): {len(set(missing))}. "
                f"{'Dry-run: no se modificaron datos.' if dry_run else ''}"
            )
        )

    def _collect_ids(self, options) -> List[int]:
        ids: List[int] = []
        raw_args = options.get("ids") or []

        def extend_from_iterable(raw_values: Iterable[str]):
            for raw in raw_values:
                tokens = re.split(r"[\s,]+", str(raw))
                for token in tokens:
                    if not token:
                        continue
                    try:
                        pk = int(token)
                    except ValueError as exc:  # pragma: no cover - error path
                        raise CommandError(f"ID inválido: '{token}'. Debe ser entero.") from exc
                    if pk not in ids:
                        ids.append(pk)

        extend_from_iterable(raw_args)

        path = options.get("ids_file")
        if path:
            try:
                with open(path, encoding="utf-8") as handler:
                    file_content = handler.read()
            except OSError as exc:  # pragma: no cover - dependiente de FS
                raise CommandError(f"No se pudo leer el archivo '{path}': {exc}") from exc

            extend_from_iterable([file_content])

        return ids

    @staticmethod
    def _chunk(values: List[int], size: int) -> Iterable[List[int]]:
        for start in range(0, len(values), size):
            yield values[start : start + size]

