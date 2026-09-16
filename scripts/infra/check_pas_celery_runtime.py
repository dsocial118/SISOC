"""Prueba de humo local: requiere un broker aislado y PAS_MONTHLY_ENABLED=false.

Inicia un worker descartable, publica la tarea deshabilitada del scheduler y
verifica la entrega. No usar con un broker que tenga trabajo productivo pendiente.
"""

import os
import subprocess
import tempfile
import time
from pathlib import Path


def main():
    if os.environ.get("PAS_CELERY_ISOLATED_SMOKE") != "1":
        raise RuntimeError("Usar solo con un broker de smoke explícitamente aislado")
    os.environ["PAS_MONTHLY_ENABLED"] = "false"
    from config.celery import app  # pylint: disable=import-outside-toplevel

    with tempfile.TemporaryDirectory() as directory:
        log = Path(directory) / "worker.log"
        with log.open("w", encoding="utf-8") as output:
            worker = subprocess.Popen(
                [
                    "celery",
                    "-A",
                    "config.celery:app",
                    "worker",
                    "-Q",
                    "pas",
                    "--concurrency=1",
                    "--loglevel=INFO",
                ],
                stdout=output,
                stderr=subprocess.STDOUT,
            )
            try:
                result = app.send_task("pas.tasks.schedule_month", queue="pas")
                for _ in range(40):
                    content = log.read_text(encoding="utf-8")
                    if f"pas.tasks.schedule_month[{result.id}] succeeded" in content:
                        print("Celery + Redis: tarea recibida y completada")
                        return
                    if worker.poll() is not None:
                        break
                    time.sleep(1)
                raise RuntimeError(log.read_text(encoding="utf-8"))
            finally:
                worker.terminate()
                worker.wait(timeout=20)


if __name__ == "__main__":
    main()
