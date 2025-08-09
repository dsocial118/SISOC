# centrodefamilia/management/commands/reprocess_cabal.py
from django.core.management.base import BaseCommand, CommandError
from centrodefamilia.services.informe_cabal_reprocess import (
    reprocesar_registros_rechazados,
)


class Command(BaseCommand):
    help = "Reprocesa registros CABAL rechazados por no-coincidencia de centro."

    def add_arguments(self, parser):
        parser.add_argument("--archivo", type=int, help="ID de CabalArchivo a reprocesar.")
        parser.add_argument("--centro", type=int, help="ID de Centro (opcional, filtra por ese código).")
        parser.add_argument("--only-pago-rechazado", action="store_true",
                            help="Solo registros con motivo_rechazo != '0'.")
        parser.add_argument("--commit", action="store_true",
                            help="Aplica cambios (por defecto hace dry-run).")
        parser.add_argument("--batch-size", type=int, default=500, help="Tamaño de lote.")

    def handle(self, *args, **opts):
        res = reprocesar_registros_rechazados(
            archivo_id=opts.get("archivo"),
            centro_id=opts.get("centro"),
            only_pago_rechazado=opts.get("only_pago_rechazado") or False,
            dry_run=not opts.get("commit"),
            batch_size=opts.get("batch_size") or 500,
        )
        if not res.get("ok"):
            raise CommandError(res.get("error") or "Error en reproceso.")

        mode = "DRY-RUN" if res["dry_run"] else "COMMIT"
        self.stdout.write(self.style.SUCCESS(f"[{mode}] Registros candidatos: {res['total_candidatos']}"))
        self.stdout.write(self.style.SUCCESS(f"[{mode}] Registros actualizados: {res['actualizados']}"))
        self.stdout.write(self.style.SUCCESS(f"Archivos afectados: {res['archivos_afectados']}"))
