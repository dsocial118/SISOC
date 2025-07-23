# comedores/management/commands/sync_comedores_gestionar.py
from itertools import islice
import os
import time
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from django.core.management.base import BaseCommand
from django.db import reset_queries
from django.db.models import Q

from comedores.models import Comedor
from comedores.tasks import build_comedor_payload

LOG = logging.getLogger(__name__)
TIMEOUT = 30
MAX_WORKERS = 5
BATCH_SIZE = 100
RETRIES = 3
SLEEP_BETWEEN_RETRIES = 3  # seconds


def send(payload):
    url = os.getenv("GESTIONAR_API_CREAR_COMEDOR")
    headers = {"applicationAccessKey": os.getenv("GESTIONAR_API_KEY")}
    for attempt in range(1, RETRIES + 1):
        try:
            r = requests.post(url, json=payload, headers=headers, timeout=TIMEOUT)
            r.raise_for_status()
            return True, None
        except Exception as e:
            if attempt < RETRIES:
                time.sleep(SLEEP_BETWEEN_RETRIES * attempt)
            else:
                return False, e


class Command(BaseCommand):
    help = "Sincroniza PROGRAMAS e Imagen (foto_legajo) de todos los Comedores que tengan esos datos."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run", action="store_true", help="No envía nada, solo muestra IDs."
        )
        parser.add_argument(
            "--limit", type=int, default=None, help="Limitar cantidad de comedores."
        )
        parser.add_argument(
            "--workers", type=int, default=MAX_WORKERS, help="Threads para requests."
        )
        parser.add_argument(
            "--batch-size", type=int, default=BATCH_SIZE, help="Tamaño de lote."
        )

    def handle(self, *args, **opts):
        dry = opts["dry_run"]
        limit = opts["limit"]
        workers = opts["workers"]
        batch_size = opts["batch_size"]

        qs = (
            Comedor.objects.filter(
                Q(programa__isnull=False) | Q(foto_legajo__isnull=False)
            )
            .only("id", "programa", "foto_legajo")  # minimiza carga
            .order_by("id")
        )
        if limit:
            qs = qs[:limit]

        total = qs.count()
        self.stdout.write(
            self.style.NOTICE(f"Encontrados {total} comedores para sync.")
        )
        if dry:
            self.stdout.write(", ".join(map(str, qs.values_list("id", flat=True))))
            return

        success, fail = 0, 0

        def chunked(iterable, size):
            it = iter(iterable)
            while True:
                batch = list(islice(it, size))
                if not batch:
                    break
                yield batch

        for batch in chunked(qs.iterator(chunk_size=batch_size), batch_size):
            payloads = [(c.id, build_comedor_payload(c)) for c in batch]

            with ThreadPoolExecutor(max_workers=workers) as ex:
                future_map = {ex.submit(send, p): cid for cid, p in payloads}
                for fut in as_completed(future_map):
                    cid = future_map[fut]
                    ok, err = fut.result()
                    if ok:
                        success += 1
                    else:
                        fail += 1
                        LOG.error("Fallo sync comedor %s: %s", cid, err)

            reset_queries()  # liberar memoria en loops largos

            self.stdout.write(
                self.style.SUCCESS(
                    f"Lote OK. Acumulado: {success} éxitos, {fail} fallos"
                )
            )

        self.stdout.write(self.style.SUCCESS(f"FIN. Éxitos: {success}  Fallos: {fail}"))
