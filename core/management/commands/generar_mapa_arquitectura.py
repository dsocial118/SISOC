"""Regenera las salidas informativas del mapa de arquitectura."""

import logging
import subprocess
import sys
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

logger = logging.getLogger(__name__)

# El arranque sólo produce el grafo de runtime; los artefactos de docs/ se
# actualizan a mano con `--docs` para no ensuciar el checkout en cada deploy.
SALIDAS = ("var/arquitectura/grafo.json",)


class Command(BaseCommand):
    help = "Regenera el mapa de arquitectura del sistema."

    def add_arguments(self, parser):
        parser.add_argument(
            "--check",
            action="store_true",
            help="Verifica que existan todas las salidas después de generar el mapa.",
        )

    def handle(self, *args, **options):
        base_dir = Path(settings.BASE_DIR)
        try:
            result = subprocess.run(
                [
                    sys.executable,
                    str(base_dir / "scripts/arquitectura/generar_mapa.py"),
                ],
                cwd=settings.BASE_DIR,
                timeout=120,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
            )
            if result.stdout:
                logger.info("Mapa de arquitectura: %s", result.stdout.rstrip())
            if result.stderr:
                logger.warning("Mapa de arquitectura: %s", result.stderr.rstrip())
            if result.returncode:
                raise CommandError(
                    f"El generador del mapa falló (exit={result.returncode})."
                )
            if options["check"]:
                faltantes = [
                    ruta for ruta in SALIDAS if not (base_dir / ruta).is_file()
                ]
                if faltantes:
                    raise CommandError(
                        "Faltan salidas del mapa: " + ", ".join(faltantes)
                    )
        except (OSError, subprocess.SubprocessError) as exc:
            logger.error("No se pudo generar el mapa de arquitectura: %s", exc)
            raise CommandError(f"No se pudo generar el mapa: {exc}") from exc

        self.stdout.write(
            self.style.SUCCESS("Generación del mapa de arquitectura finalizada.")
        )
