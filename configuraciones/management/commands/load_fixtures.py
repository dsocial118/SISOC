import os
import subprocess
import time
import json
from concurrent.futures import ThreadPoolExecutor
import pymysql
from django.core.management.base import BaseCommand
from django.apps import apps


class Command(BaseCommand):
    help = "Carga los fixtures condicionalmente y limpia el código si es necesario."

    def handle(self, *args, **options):
        # Ejecutar los comandos de Django (migraciones, fixtures, etc.)
        self.run_django_commands()

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
            print(f"⚠️  Error al leer el fixture {fixture_path}: {e}")
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
            print(f"⚠️  Error al consultar el modelo {model_label}: {e}")
            return False

    def should_load_fixture(self, fixture_path):
        """
        Retorna True si todos los modelos referenciados en el fixture están vacíos.
        """
        models = self.get_models_from_fixture(fixture_path)
        if not models:
            print(f"⚠️  No se encontraron modelos en el fixture: {fixture_path}")
            return False
        return all(self.model_is_empty(m) for m in models)

    def load_fixture(self, file):
        """
        Carga un fixture solo si los modelos asociados están vacíos.
        """
        if self.should_load_fixture(file):
            print(f"📥 Cargando fixture: {file}")
            subprocess.run(["python", "manage.py", "loaddata", file])
        else:
            print(f"⏩ Omitiendo fixture: {file} (los modelos ya tienen datos)")

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
            executor.map(self.load_fixture, fixtures)

    def run_django_commands(self):
        """
        Ejecuta los comandos de preparación de Django: migraciones, carga de fixtures y configuración inicial.
        """
        subprocess.run(["python", "manage.py", "makemigrations"])
        subprocess.run(["python", "manage.py", "migrate", "--noinput"])
        self.load_fixtures()
        subprocess.run(["python", "manage.py", "create_local_superuser"])
        subprocess.run(["python", "manage.py", "create_groups"])
        self.run_server()

    def run_server(self):
        """
        Inicia el servidor de Django. Usa Gunicorn en producción o el servidor de desarrollo si no.
        """
        environment = os.getenv("ENVIRONMENT", "dev").lower()

        if environment == "prd":
            print("🚀 Iniciando Django en modo producción con Gunicorn...")
            subprocess.run(
                [
                    "gunicorn",
                    "config.asgi:application",
                    "-k",
                    "uvicorn.workers.UvicornWorker",
                    "-b",
                    "0.0.0.0:8000",
                    "--workers",
                    "4",
                    "--threads",
                    "2",
                    "--log-level",
                    "info",
                ]
            )
        else:
            print("🧪 Iniciando Django en modo desarrollo...")
            subprocess.run(["python", "manage.py", "runserver", "0.0.0.0:8000"])
