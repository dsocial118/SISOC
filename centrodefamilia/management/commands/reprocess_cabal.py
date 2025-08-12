# centrodefamilia/management/commands/reprocess_cabal.py
from django.core.management.base import BaseCommand, CommandError
from centrodefamilia.services.informe_cabal_reprocess import (
    reprocesar_registros_rechazados_por_codigo,
)


class Command(BaseCommand):
    help = (
        "Reprocesa registros CABAL rechazados (no_coincidente=True) para un código de centro (NroComercio). "
        "Por defecto corre en DRY-RUN; aplica cambios con --commit."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--codigo",
            required=True,
            help="Código de centro (NroComercio) a reprocesar.",
        )
        parser.add_argument(
            "--commit",
            action="store_true",
            help="Aplica cambios (por defecto hace dry-run).",
        )

    def handle(self, *args, **opts):
        codigo = (opts.get("codigo") or "").strip()
        dry_run = not opts.get("commit")

        if not codigo:
            raise CommandError("Debe indicar un código de centro con --codigo")

        try:
            res = reprocesar_registros_rechazados_por_codigo(
                codigo=codigo, dry_run=dry_run
            )
        except Exception as exc:
            raise CommandError(str(exc) or "Error en reproceso.") from exc

        mode = "DRY-RUN" if dry_run else "COMMIT"
        self.stdout.write(self.style.SUCCESS(f"[{mode}] Código: {codigo}"))
        self.stdout.write(
            self.style.SUCCESS(
                f"[{mode}] Registros detectados: {res.get('procesados', 0)}"
            )
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"[{mode}] Registros impactados: {res.get('impactados', 0)}"
            )
        )

        por_archivo = res.get("por_archivo", {})
        if por_archivo:
            self.stdout.write(
                self.style.SUCCESS(f"[{mode}] Desglose por archivo: {por_archivo}")
            )
