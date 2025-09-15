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
                    comedor_id = int(comedor_str) + 100000  # Ajuste al ID externo
                except ValueError:
                    self.stderr.write(
                        f"[Fila {reader.line_num}] id externo inválido: '{comedor_str}'. Debe ser un entero (campo comedor_id de Comedor)."
                    )
                    other_errors += 1
                    continue

                try:
                    comedor = Comedor.objects.get(id=comedor_id)
                except Comedor.DoesNotExist:
                    self.stderr.write(
                        f"[Fila {reader.line_num}] Comedor con comedor_id={comedor_id} no existe."
                    )
                    other_errors += 1
                    continue
                except Comedor.MultipleObjectsReturned:
                    self.stderr.write(
                        f"[Fila {reader.line_num}] Existen múltiples comedores con comedor_id={comedor_id}."
                    )
                    other_errors += 1
                    continue

                # Construye el relevamiento en estado activo y valida duplicados activos
                rv = Relevamiento(
                    territorial_uid=uid,
                    territorial_nombre=nombre,
                    comedor=comedor,
                    fecha_visita=timezone.now(),
                    estado="Visita pendiente",
                )

                try:
                    # Validación explícita para clasificar correctamente los saltos por activo
                    rv.validate_relevamientos_activos()
                except (CoreValidationError, FormsValidationError) as e:
                    msg = str(e)
                    if "Ya existe un relevamiento activo" in msg:
                        self.stderr.write(
                            f"[Fila {reader.line_num}] Omitido: ya existe relevamiento activo para el comedor con comedor_id {comedor_id}."
                        )
                        skipped_active += 1
                        continue
                    # Cualquier otra validación se trata como otro error
                    self.stderr.write(
                        f"[Fila {reader.line_num}] Error de validación: {e}"
                    )
                    other_errors += 1
                    continue

                try:
                    rv.save()  # dispara signals y validaciones del modelo
                    created_ok += 1
                except (CoreValidationError, FormsValidationError) as e:
                    msg = str(e)
                    if "Ya existe un relevamiento activo" in msg:
                        self.stderr.write(
                            f"[Fila {reader.line_num}] Omitido: ya existe relevamiento activo para el comedor con comedor_id {comedor_id}."
                        )
                        skipped_active += 1
                    else:
                        self.stderr.write(
                            f"[Fila {reader.line_num}] Error al crear relevamiento: {e}"
                        )
                        other_errors += 1
                except Exception as e:  # pylint: disable=broad-except
                    self.stderr.write(f"[Fila {reader.line_num}] Error inesperado: {e}")
                    other_errors += 1

            self.stdout.write(
                self.style.SUCCESS(
                    "Importación finalizada. "
                    f"Creados: {created_ok}. "
                    f"Omitidos por activo: {skipped_active}. "
                    f"Errores: {other_errors}."
                )
            )
