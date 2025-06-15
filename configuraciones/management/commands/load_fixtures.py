import os
import json
from concurrent.futures import ThreadPoolExecutor
from django.core.management.base import BaseCommand
from django.apps import apps
import subprocess


class Command(BaseCommand):
    help = "Carga los fixtures condicionalmente o forzadamente."

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Fuerza la carga de los fixtures incluso si hay datos en los modelos.",
        )

    def handle(self, *args, **options):
        self.force = options["force"]
        self.load_fixtures()

    def get_models_from_fixture(self, fixture_path):
        """
        Extrae los modelos referenciados en un archivo de fixture JSON.
        Devuelve un conjunto de etiquetas 'app_label.ModelName'.
        """
        try:
            with open(fixture_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return {entry["model"] for entry in data if "model" in entry}
        except Exception as e:
            self.stderr.write(f"⚠️  Error al leer el fixture {fixture_path}: {e}")
            return set()

    def model_is_empty(self, model_label):
        """
        Verifica si un modelo está vacío (sin registros).
        """
        try:
            app_label, model_name = model_label.split(".")
            model = apps.get_model(app_label, model_name)
            return model.objects.count() == 0
        except Exception as e:
            self.stderr.write(f"⚠️  Error al consultar el modelo {model_label}: {e}")
            return False

    def should_load_fixture(self, fixture_path):
        """
        Retorna True si todos los modelos referenciados en el fixture están vacíos,
        o si se forzó la carga.
        """
        if self.force:
            return True

        models = self.get_models_from_fixture(fixture_path)
        if not models:
            self.stderr.write(
                f"⚠️  No se encontraron modelos en el fixture: {fixture_path}"
            )
            return False
        return all(self.model_is_empty(m) for m in models)

    def load_fixture(self, file):
        """
        Carga un fixture si corresponde según el estado de la base o la opción --force.
        """
        if self.should_load_fixture(file):
            subprocess.run(["python", "manage.py", "loaddata", file])

    def load_fixtures(self):
        """
        Busca y carga todos los fixtures en carpetas llamadas 'fixtures' del proyecto.
        La carga es concurrente y condicional según el estado de la base.
        """
        fixtures = []
        for root, dirs, _ in os.walk("."):
            if "fixtures" in dirs:
                fixtures_dir = os.path.join(root, "fixtures")
                fixtures.extend(
                    [
                        os.path.join(fixtures_dir, file)
                        for file in os.listdir(fixtures_dir)
                        if file.endswith(".json")
                    ]
                )

        with ThreadPoolExecutor() as executor:
            self.stdout.write(f"📥 Cargando fixtures...")
            executor.map(self.load_fixture, fixtures)
