from django.core.management.base import BaseCommand
from core.debug_queries import debug_all_views, debug_ciudadano_detail_queries


class Command(BaseCommand):
    help = "Depura las queries de las vistas del sistema SISOC"

    def add_arguments(self, parser):
        parser.add_argument(
            "--view",
            type=str,
            help="Depurar solo una vista específica (por ejemplo: ciudadanos)",
            default="all",
        )
        parser.add_argument(
            "--verbose",
            action="store_true",
            help="Mostrar información detallada de las queries",
        )

    def handle(self, *args, **options):
        view_type = options["view"]

        self.stdout.write(self.style.SUCCESS("🔍 Iniciando depuración de queries...\n"))

        if view_type == "ciudadanos":
            self.stdout.write("Depurando CiudadanosDetailView...")
            debug_ciudadano_detail_queries()
        elif view_type == "all":
            self.stdout.write("Depurando todas las vistas...")
            results = debug_all_views()

            if results:
                self.stdout.write(
                    self.style.SUCCESS("\n✅ Depuración completada exitosamente.")
                )
            else:
                self.stdout.write(self.style.ERROR("\n❌ Error durante la depuración."))
        else:
            self.stdout.write(
                self.style.ERROR(
                    f'Vista "{view_type}" no reconocida. Use "ciudadanos" o "all".'
                )
            )
