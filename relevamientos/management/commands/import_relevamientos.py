import csv
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from django.core.management.base import BaseCommand
from django.core.exceptions import ValidationError as CoreValidationError
from django.forms import ValidationError as FormsValidationError
from django.db.models.signals import post_save
from django.utils import timezone
from relevamientos.models import Relevamiento, Comedor
from relevamientos.tasks import AsyncSendRelevamientoToGestionar
import relevamientos.signals as relev_signals


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

            batch_size = int(options.get("batch_size") or 200)
            max_workers = int(options.get("signal_workers") or 5)
            buffer: list[dict] = []

            def drain_created(created_ids: list[int]):
                if not created_ids:
                    return
                # Ejecuta el efecto del signal con concurrencia limitada para no saturar conexiones
                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    futures = [
                        executor.submit(
                            lambda rid: AsyncSendRelevamientoToGestionar(rid).run(), rid
                        )
                        for rid in created_ids
                    ]
                    for fut in as_completed(futures):
                        try:
                            fut.result()
                        except Exception as exc:  # noqa: BLE001
                            self.stderr.write(
                                f"[Post-save] Error al enviar relevamiento a GESTIONAR: {exc}"
                            )

            def process_batch(rows: list[dict]):
                nonlocal created_ok, skipped_active, other_errors
                if not rows:
                    return

                # Buscar comedores por id en una sola query
                externos = [r["id_externo"] for r in rows]
                comedores_qs = Comedor.objects.filter(id__in=externos)

                # Manejar posibles duplicados de id_externo
                comedores_by_externo = {}
                duplicates = set()
                for c in comedores_qs:
                    key = c.id_externo
                    if key in comedores_by_externo:
                        duplicates.add(key)
                    else:
                        comedores_by_externo[key] = c

                # Precompute activos por pk de comedor
                pk_unicos = [
                    c.id for k, c in comedores_by_externo.items() if k not in duplicates
                ]
                activos = set(
                    Relevamiento.objects.filter(
                        comedor_id__in=pk_unicos,
                        estado__in=["Pendiente", "Visita pendiente"],
                    ).values_list("comedor_id", flat=True)
                )

                created_ids: list[int] = []

                for r in rows:
                    line = r["line"]
                    nombre = r["nombre"]
                    uid = r["uid"]
                    id_externo = r["id_externo"]

                    if id_externo in duplicates:
                        self.stderr.write(
                            f"[Fila {line}] Existen múltiples comedores con id_externo={id_externo}."
                        )
                        other_errors += 1
                        continue

                    comedor = comedores_by_externo.get(id_externo)
                    if not comedor:
                        self.stderr.write(
                            f"[Fila {line}] Comedor con id_externo={id_externo} no existe."
                        )
                        other_errors += 1
                        continue

                    if comedor.id in activos:
                        self.stderr.write(
                            f"[Fila {line}] Omitido: ya existe relevamiento activo para el comedor con id_externo {id_externo}."
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
                        rv.save()  # Dispara validaciones del modelo (signal desconectado)
                        created_ok += 1
                        created_ids.append(rv.id)
                    except (CoreValidationError, FormsValidationError) as e:
                        msg = str(e)
                        if "Ya existe un relevamiento activo" in msg:
                            self.stderr.write(
                                f"[Fila {line}] Omitido: ya existe relevamiento activo para el comedor con id_externo {id_externo}."
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

                # Ejecutar el efecto del signal con control de concurrencia
                drain_created(created_ids)

            # Desconectar temporalmente el signal para limitar concurrencia externa
            try:
                post_save.disconnect(
                    receiver=relev_signals.send_relevamiento_to_gestionar,
                    sender=Relevamiento,
                )
            except Exception:
                pass

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
                    id_externo = int(comedor_str)
                except ValueError:
                    self.stderr.write(
                        f"[Fila {reader.line_num}] id externo inválido: '{comedor_str}'. Debe ser un entero (campo id_externo de Comedor)."
                    )
                    other_errors += 1
                    continue

                buffer.append(
                    {
                        "line": reader.line_num,
                        "nombre": nombre,
                        "uid": uid,
                        "id_externo": id_externo,
                    }
                )

                if len(buffer) >= batch_size:
                    process_batch(buffer)
                    buffer.clear()

            # Procesar remanente
            if buffer:
                process_batch(buffer)
                buffer.clear()

            # Reconectar signal al finalizar
            try:
                post_save.connect(
                    receiver=relev_signals.send_relevamiento_to_gestionar,
                    sender=Relevamiento,
                )
            except Exception:
                pass

            self.stdout.write(
                self.style.SUCCESS(
                    "Importación finalizada. "
                    f"Creados: {created_ok}. "
                    f"Omitidos por activo: {skipped_active}. "
                    f"Errores: {other_errors}."
                )
            )
