"""
Management command: recuperar_nominas_csv

Asigna comedor_id (y opcionalmente admision_id) a nóminas huérfanas
a partir de un CSV de backup previo a la migración 0024.

El CSV debe tener al menos las columnas:
  id, comedor_id, admision_id_sugerida

Uso:
  python manage.py recuperar_nominas_csv /ruta/al/backup.csv
  python manage.py recuperar_nominas_csv /ruta/al/backup.csv --dry-run
  python manage.py recuperar_nominas_csv /ruta/al/backup.csv --batch-size 2000

Lógica:
  - Programa 3/4 (Abordaje comunitario): asigna solo comedor_id,
    admision queda null (nueva lógica de nóminas directas).
  - Programa 2 (Alimentar comunidad): asigna comedor_id y,
    si admision_id_sugerida tiene valor, también admision_id.
  - Usa Nomina.all_objects (incluye soft-deleted).
  - No toca ningún otro campo (estado, ciudadano, observaciones, etc.).
"""

import csv
from collections import defaultdict

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from comedores.models import Comedor, Nomina

PROGRAMAS_SIN_ADMISION = {3, 4}


class Command(BaseCommand):
    help = "Recupera comedor_id en nóminas huérfanas desde un CSV de backup."

    def add_arguments(self, parser):
        parser.add_argument("csv_path", help="Ruta al archivo CSV de backup.")
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Muestra qué se haría sin aplicar cambios.",
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=5000,
            help="Tamaño del batch de actualización (default: 5000).",
        )

    def handle(self, *args, **options):
        csv_path = options["csv_path"]
        dry_run = options["dry_run"]
        batch_size = options["batch_size"]

        if dry_run:
            self.stdout.write(
                self.style.WARNING("Modo dry-run: no se aplican cambios.")
            )

        # 1. Leer CSV y agrupar por comedor_id
        # nominas_por_comedor: {comedor_id: [(nomina_id, admision_id_sugerida), ...]}
        nominas_por_comedor = defaultdict(list)
        total_csv = 0

        try:
            with open(csv_path, encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    nomina_id = int(row["id"])
                    comedor_id = int(row["comedor_id"])
                    admision_raw = row.get("admision_id_sugerida", "").strip()
                    admision_id = int(admision_raw) if admision_raw else None
                    nominas_por_comedor[comedor_id].append((nomina_id, admision_id))
                    total_csv += 1
        except FileNotFoundError as exc:
            raise CommandError(f"Archivo no encontrado: {csv_path}") from exc
        except (KeyError, ValueError) as exc:
            raise CommandError(f"Error al leer el CSV: {exc}") from exc

        self.stdout.write(
            f"CSV leído: {total_csv} registros en "
            f"{len(nominas_por_comedor)} comedores únicos."
        )

        # 2. Obtener programa de cada comedor (una sola query)
        comedores_qs = Comedor.all_objects.filter(
            id__in=list(nominas_por_comedor.keys())
        ).values("id", "programa_id", "nombre")
        comedor_data = {c["id"]: c for c in comedores_qs}

        comedores_no_encontrados = set(nominas_por_comedor) - set(comedor_data)
        if comedores_no_encontrados:
            self.stdout.write(
                self.style.WARNING(
                    f"Comedores no encontrados en DB ({len(comedores_no_encontrados)}): "
                    f"{sorted(comedores_no_encontrados)}"
                )
            )

        # 3. Procesar por comedor
        total_actualizado = 0
        total_omitido = 0

        with transaction.atomic():
            for comedor_id, nominas in nominas_por_comedor.items():
                if comedor_id not in comedor_data:
                    total_omitido += len(nominas)
                    continue

                programa_id = comedor_data[comedor_id]["programa_id"]
                usa_admision = programa_id not in PROGRAMAS_SIN_ADMISION

                nomina_ids = [n[0] for n in nominas]
                admision_map = {n[0]: n[1] for n in nominas}

                for i in range(0, len(nomina_ids), batch_size):
                    batch_ids = nomina_ids[i : i + batch_size]
                    qs_base = Nomina.all_objects.filter(id__in=batch_ids)

                    if usa_admision:
                        # Para prog 2: agrupar por admision_id_sugerida
                        por_admision = defaultdict(list)
                        for nid in batch_ids:
                            por_admision[admision_map.get(nid)].append(nid)

                        for admision_id, ids in por_admision.items():
                            qs = Nomina.all_objects.filter(id__in=ids)
                            kwargs = {"comedor_id": comedor_id}
                            if admision_id:
                                kwargs["admision_id"] = admision_id
                            if not dry_run:
                                updated = qs.update(**kwargs)
                            else:
                                updated = qs.count()
                            total_actualizado += updated
                    else:
                        # Para prog 3/4: solo comedor_id, admision queda null
                        if not dry_run:
                            updated = qs_base.update(comedor_id=comedor_id)
                        else:
                            updated = qs_base.count()
                        total_actualizado += updated

            if dry_run:
                transaction.set_rollback(True)

        modo = "(dry-run) " if dry_run else ""
        self.stdout.write(
            self.style.SUCCESS(
                f"{modo}Actualizados: {total_actualizado} | "
                f"Omitidos (comedor no encontrado): {total_omitido}"
            )
        )
