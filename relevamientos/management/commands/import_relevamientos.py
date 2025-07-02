import csv
from django.core.management.base import BaseCommand
from django.core.exceptions import ValidationError
from relevamientos.models import Relevamiento, Comedor


class Command(BaseCommand):
    help = "Importa Relevamiento desde CSV, respetando signals y validaciones."

    def add_arguments(self, parser):
        parser.add_argument("csv_path", type=str, help="Ruta al archivo CSV")

    def handle(self, *args, **options):
        path = options["csv_path"]
        with open(path, newline="", encoding="utf-8") as f:
            sample = f.read(2048)
            f.seek(0)
            # Detecta coma o punto y coma
            dialect = csv.Sniffer().sniff(sample, delimiters=",;")
            reader = csv.DictReader(f, dialect=dialect)

            created = errors = 0
            for row in reader:
                uid = row.get("ID GESTIONAR")
                comedor_id = row.get("ID Comedor")
                try:
                    comedor = Comedor.objects.get(pk=comedor_id)
                    rv = Relevamiento(territorial_uid=uid, comedor=comedor)
                    rv.save()  # dispara signals y tu lógica de save()
                    created += 1
                except Comedor.DoesNotExist:
                    self.stderr.write(
                        f"[Fila {reader.line_num}] Comedor {comedor_id} no existe."
                    )
                    errors += 1
                except ValidationError as e:
                    self.stderr.write(f"[Fila {reader.line_num}] Error: {e}")
                    errors += 1

            self.stdout.write(
                self.style.SUCCESS(
                    f"Relevamientos creados: {created}. Errores: {errors}"
                )
            )
