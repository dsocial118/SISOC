from datetime import date

from django.core.management.base import BaseCommand, CommandError

from pas.services.supervivencia_service import sincronizar_supervivencia_pas


class Command(BaseCommand):
    help = "Contrasta diariamente el padrón PAS con RENAPER."

    def add_arguments(self, parser):
        parser.add_argument(
            "--fecha",
            help="Fecha de control en formato AAAA-MM-DD. Por defecto usa hoy.",
        )
        parser.add_argument(
            "--forzar",
            action="store_true",
            help="Repite controles que ya fueron registrados para la fecha.",
        )
        parser.add_argument(
            "--limite",
            type=int,
            help="Limita la cantidad de titulares a consultar.",
        )

    def handle(self, *args, **options):
        fecha_consulta = None
        if options["fecha"]:
            try:
                fecha_consulta = date.fromisoformat(options["fecha"])
            except ValueError as exc:
                raise CommandError("--fecha debe usar el formato AAAA-MM-DD.") from exc
        if options["limite"] is not None and options["limite"] < 1:
            raise CommandError("--limite debe ser mayor que cero.")

        resumen = sincronizar_supervivencia_pas(
            fecha_consulta=fecha_consulta,
            forzar=options["forzar"],
            limite=options["limite"],
        )
        self.stdout.write(
            self.style.SUCCESS(
                "Control RENAPER PAS finalizado: "
                f"total={resumen['total']}, "
                f"vivas={resumen['vigentes']}, "
                f"fallecidas={resumen['fallecidas']}, "
                f"sin_coincidencia={resumen['no_encontradas']}, "
                f"errores={resumen['errores']}, "
                f"omitidas={resumen['omitidas']}."
            )
        )
