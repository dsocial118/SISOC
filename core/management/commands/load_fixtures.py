import os
import json
from django.core.management.base import BaseCommand
from django.apps import apps
from django.core import serializers
from django.db import transaction


class Command(BaseCommand):
    help = "Carga fixtures sin borrar: actualiza por PK si existe, crea si no. Nunca borra."

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Ignora chequeos de vacíos y carga igual (sin borrar nada).",
        )

    def handle(self, *args, **options):
        self.force = options["force"]
        self.load_fixtures()

    def get_models_from_fixture(self, fixture_path):
        try:
            with open(fixture_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return {entry.get("model") for entry in data if "model" in entry}
        except Exception as e:
            self.stderr.write(f"⚠️  Error al leer {fixture_path}: {e}")
            return set()

    def model_is_empty(self, model_label):
        try:
            app_label, model_name = model_label.split(".")
            model = apps.get_model(app_label, model_name)
            return model.objects.count() == 0
        except Exception as e:
            self.stderr.write(f"⚠️  Error al consultar {model_label}: {e}")
            return False

    def should_load_fixture(self, fixture_path):
        if self.force:
            return True
        models = self.get_models_from_fixture(fixture_path)
        if not models:
            self.stderr.write(f"⚠️  Sin modelos en: {fixture_path}")
            return False
        # Cargar si al menos uno de los modelos mencionados está vacío
        # (permite completar tablas faltantes sin bloquear toda la fixture).
        return any(self.model_is_empty(m) for m in models)

    def upsert_fixture(self, fixture_path):
        """
        Deserializa y guarda: si PK existe → UPDATE; si no → INSERT.
        M2M y FKs los maneja el Deserializer. Nunca borra.
        """
        try:
            with open(fixture_path, "r", encoding="utf-8") as f:
                objects = list(
                    serializers.deserialize("json", f, ignorenonexistent=True)
                )
        except Exception as e:
            self.stderr.write(f"❌ No se pudo deserializar {fixture_path}: {e}")
            return

        created, updated, failed = 0, 0, 0
        for obj in objects:
            try:
                model = obj.object.__class__
                pk_field = obj.object._meta.pk.attname
                pk_value = getattr(obj.object, pk_field, None)
                existed_before = bool(pk_value) and model.objects.filter(
                    pk=pk_value
                ).exists()

                # Guardar cada objeto en su propia transacción para evitar que un
                # error deje la conexión marcada para rollback y bloquee el resto.
                with transaction.atomic():
                    obj.save()  # maneja FKs y M2M luego del save

                if existed_before:
                    updated += 1
                else:
                    created += 1
            except Exception as e:
                failed += 1
                self.stderr.write(f"⚠️  Falló guardar registro de {fixture_path}: {e}")

        self.stdout.write(
            f"✅ {fixture_path}: created={created}, updated≈{updated}, failed={failed}"
        )

    def load_fixtures(self):
        fixtures = []
        for root, dirs, _ in os.walk("."):
            if "fixtures" in dirs:
                fixtures_dir = os.path.join(root, "fixtures")
                for file in os.listdir(fixtures_dir):
                    if file.endswith(".json"):
                        fixtures.append(os.path.join(fixtures_dir, file))

        fixtures = sorted(set(fixtures))
        if not fixtures:
            self.stdout.write("ℹ️  No se encontraron fixtures.")
            return

        self.stdout.write("📥 Cargando fixtures (sin borrar nada)...")
        for fx in fixtures:
            if self.should_load_fixture(fx):
                self.upsert_fixture(fx)
