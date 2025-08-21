from itertools import islice
import os
import time
import json
import logging
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from django.core.management.base import BaseCommand
from django.db import reset_queries
from django.db.models import Q

from comedores.models import Comedor
from comedores.tasks import build_comedor_payload

LOG = logging.getLogger("django")
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
    help = "Sincroniza TODOS los campos del Comedor (payload completo)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run", action="store_true", help="No envía nada, solo muestra IDs."
        )
        parser.add_argument(
            "--comedor-id",
            type=int,
            dest="comedor_id",
            help="ID específico de Comedor a sincronizar. Si se especifica, ignora --limit.",
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
        parser.add_argument(
            "--verbose",
            action="store_true",
            help="Loguea cada resultado y genera JSON.",
        )
        parser.add_argument(
            "--out-file",
            type=str,
            default=None,
            help="Ruta del JSON de resultados (solo con --verbose).",
        )
        parser.add_argument(
            "--action",
            type=str,
            default="Add",
            choices=("Add", "Update"),
            help='Valor para payload["Action"].',
        )

    def handle(self, *args, **opts):
        dry = opts["dry_run"]
        comedor_id = opts.get("comedor_id")
        limit = opts["limit"]
        workers = opts["workers"]
        batch_size = opts["batch_size"]
        verbose = opts["verbose"]
        out_file = opts["out_file"]
        action = opts["action"]

        # Traemos TODOS los comedores (o filtramos por id/limit). Sin .only.
        qs = (
            Comedor.objects.all()
            .select_related(
                "tipocomedor",
                "provincia",
                "municipio",
                "localidad",
                "programa",
                "organizacion",
                "referente",
                "dupla",
            )
            .order_by("id")
        )

        if comedor_id:
            qs = qs.filter(pk=comedor_id)
            self.stdout.write(
                self.style.NOTICE(f"Filtrando solo Comedor ID={comedor_id}")
            )
        elif limit:
            qs = qs[:limit]

        total = qs.count()
        self.stdout.write(
            self.style.NOTICE(f"Encontrados {total} comedores para sync.")
        )
        if dry:
            self.stdout.write(", ".join(map(str, qs.values_list("id", flat=True))))
            return

        success, fail = 0, 0
        successes, failures = [], []

        def chunked(iterable, size):
            it = iter(iterable)
            while True:
                batch = list(islice(it, size))
                if not batch:
                    break
                yield batch

        for batch in chunked(qs.iterator(chunk_size=batch_size), batch_size):
            payloads = []
            for c in batch:
                pl = build_comedor_payload(c)
                # Fuerza el Action requerido (por si la función fija "Add")
                pl["Action"] = action
                payloads.append((c.id, pl))

            with ThreadPoolExecutor(max_workers=workers) as executor:
                futures = {executor.submit(send, pl): cid for cid, pl in payloads}
                for fut in as_completed(futures):
                    cid = futures[fut]
                    ok, err = fut.result()
                    if ok:
                        success += 1
                        if verbose:
                            self.stdout.write(f"OK -> Comedor {cid}")
                            successes.append({"id": cid})
                    else:
                        fail += 1
                        err_str = repr(err)
                        LOG.error("Fallo sync comedor %s: %s", cid, err_str)
                        if verbose:
                            failures.append({"id": cid, "error": err_str})

            reset_queries()
            self.stdout.write(
                self.style.SUCCESS(
                    f"Lote OK. Acumulado: {success} éxitos, {fail} fallos"
                )
            )

        self.stdout.write(self.style.SUCCESS(f"FIN. Éxitos: {success}  Fallos: {fail}"))

        if verbose:
            if not out_file:
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                out_file = f"sync_result_{ts}.json"
            result = {
                "timestamp": datetime.now().isoformat(),
                "total": total,
                "success": success,
                "fail": fail,
                "successes": successes,
                "failures": failures,
                "action": action,
            }
            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            self.stdout.write(self.style.NOTICE(f"Resultados guardados en {out_file}"))
