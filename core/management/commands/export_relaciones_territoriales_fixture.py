from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from core.services.territorial_export import export_fixture_relations_workbook


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_FIXTURE_PATH = (
    PROJECT_ROOT / "core" / "fixtures" / "localidad_municipio_provincia.json"
)
DEFAULT_OUTPUT_PATH = PROJECT_ROOT / "out" / "relaciones_territoriales_fixture.xlsx"


class Command(BaseCommand):
    help = (
        "Genera un archivo Excel con la jerarquía provincia -> municipio -> "
        "localidad a partir de un fixture JSON."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--fixture",
            default=str(DEFAULT_FIXTURE_PATH),
            help="Ruta al fixture JSON de provincias, municipios y localidades.",
        )
        parser.add_argument(
            "--output",
            default=str(DEFAULT_OUTPUT_PATH),
            help="Ruta del archivo .xlsx de salida.",
        )

    def handle(self, *args, **options):
        fixture_path = Path(options["fixture"]).expanduser()
        output_path = Path(options["output"]).expanduser()

        if not fixture_path.is_absolute():
            fixture_path = PROJECT_ROOT / fixture_path
        if not output_path.is_absolute():
            output_path = PROJECT_ROOT / output_path

        fixture_path = fixture_path.resolve()
        output_path = output_path.resolve()

        if not fixture_path.exists():
            raise CommandError(f"No se encontró el fixture: {fixture_path}")
        if not fixture_path.is_file():
            raise CommandError(
                f"El fixture indicado no es un archivo válido: {fixture_path}"
            )

        summary = export_fixture_relations_workbook(fixture_path, output_path)

        self.stdout.write(self.style.SUCCESS(f"Archivo generado: {output_path}"))
        self.stdout.write(
            "Resumen: "
            f"{summary['provincias']} provincias, "
            f"{summary['municipios']} municipios, "
            f"{summary['localidades']} localidades, "
            f"{summary['provincias_sin_municipios']} provincias sin municipios, "
            f"{summary['municipios_sin_localidades']} municipios sin localidades, "
            f"{summary['inconsistencias']} inconsistencias."
        )
