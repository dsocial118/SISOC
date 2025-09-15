import csv
import sys
from django.core.management.base import BaseCommand
from django.core.exceptions import ValidationError as CoreValidationError
from django.forms import ValidationError as FormsValidationError
from django.utils import timezone
from relevamientos.models import Relevamiento, Comedor


class Command(BaseCommand):
    help = (
        "Importa relevamientos desde CSV con columnas: 'Nombre y apellido', "
        "'id destino' y 'id externo'. Respeta signals y validaciones."
    )

    def add_arguments(self, parser):
        parser.add_argument("csv_path", type=str, help="Ruta al archivo CSV")
        parser.add_argument(
            "--batch-size",
            type=int,
            default=200,
            help="Cantidad de filas a procesar por lote (default: 200)",
        )

    def handle(self, *args, **options):
        path = options["csv_path"]
        # Permite campos extremadamente grandes en CSV (archivos "de cualquier tamaño")
        try:
            csv.field_size_limit(sys.maxsize)
        except (OverflowError, ValueError):
            # Fallback conservador si sys.maxsize no es aceptado en la plataforma
            csv.field_size_limit(10 * 1024 * 1024)

        with open(path, newline="", encoding="utf-8-sig") as f:
            sample = f.read(2048)
            f.seek(0)
            # Detecta coma o punto y coma con fallback robusto
            try:
                dialect = csv.Sniffer().sniff(sample, delimiters=",;")
                reader = csv.DictReader(f, dialect=dialect)
            except csv.Error:
                reader = csv.DictReader(f, delimiter=",")

            created_ok = 0
            skipped_active = 0
            other_errors = 0

            batch_size = int(options.get("batch_size") or 200)
            buffer: list[dict] = []

            def process_batch(rows: list[dict]):
                nonlocal created_ok, skipped_active, other_errors
                if not rows:
                    return

                # Buscar comedores por pk en una sola query
                ids = [r["comedor_id"] for r in rows]
                comedores_qs = Comedor.objects.filter(id__in=ids)
                comedores_map = {c.id: c for c in comedores_qs}

                # Precomputar activos por pk de comedor
                activos = set(
                    Relevamiento.objects.filter(
                        comedor_id__in=list(comedores_map.keys()),
                        estado__in=["Pendiente", "Visita pendiente"],
                    ).values_list("comedor_id", flat=True)
                )

                for r in rows:
                    line = r["line"]
                    nombre = r["nombre"]
                    uid = r["uid"]
                    comedor_id = r["comedor_id"]

                    comedor = comedores_map.get(comedor_id)
                    if not comedor:
                        self.stderr.write(
                            f"[Fila {line}] Comedor con id={comedor_id} no existe."
                        )
                        other_errors += 1
                        continue

                    if comedor_id in activos:
                        self.stderr.write(
                            f"[Fila {line}] Omitido: ya existe relevamiento activo para el comedor con id {comedor_id}."
                        )
                        skipped_active += 1
                        continue

                    rv = Relevamiento(
                        territorial_uid=uid,
                        territorial_nombre=nombre,
                        comedor=comedor,
                        fecha_visita=timezone.now(),
                        estado="Visita pendiente",
                    )

                    try:
                        rv.save()  # Dispara validaciones del modelo y signals
                        created_ok += 1
                    except (CoreValidationError, FormsValidationError) as e:
                        msg = str(e)
                        if "Ya existe un relevamiento activo" in msg:
                            self.stderr.write(
                                f"[Fila {line}] Omitido: ya existe relevamiento activo para el comedor con id {comedor_id}."
                            )
                            skipped_active += 1
                        else:
                            self.stderr.write(
                                f"[Fila {line}] Error al crear relevamiento: {e}"
                            )
                            other_errors += 1
                    except Exception as e:  # pylint: disable=broad-except
                        self.stderr.write(f"[Fila {line}] Error inesperado: {e}")
                        other_errors += 1

            for row in reader:
                # Normaliza headers para ser tolerante con mayúsculas/minúsculas
                row_norm = {
                    (k or "").strip().lower(): (v or "").strip() for k, v in row.items()
                }

                nombre = row_norm.get("nombre y apellido")
                uid = row_norm.get("id destino")
                comedor_str = row_norm.get("id externo")

                if not nombre or not uid or not comedor_str:
                    self.stderr.write(
                        f"[Fila {reader.line_num}] Faltan columnas requeridas (Nombre y apellido, id destino, id externo)."
                    )
                    other_errors += 1
                    continue

                try:
                    comedor_id = int(comedor_str) + 100000
                except ValueError:
                    self.stderr.write(
                        f"[Fila {reader.line_num}] id externo inválido: '{comedor_str}'. Debe ser un entero."
                    )
                    other_errors += 1
                    continue

                buffer.append(
                    {
                        "line": reader.line_num,
                        "nombre": nombre,
                        "uid": uid,
                        "comedor_id": comedor_id,
                    }
                )

                if len(buffer) >= batch_size:
                    process_batch(buffer)
                    buffer.clear()

            # Procesar remanente
            if buffer:
                process_batch(buffer)
                buffer.clear()

            # Signals se ejecutaron normalmente durante la creación

            self.stdout.write(
                self.style.SUCCESS(
                    "Importación finalizada. "
                    f"Creados: {created_ok}. "
                    f"Omitidos por activo: {skipped_active}. "
                    f"Errores: {other_errors}."
                )
            )
