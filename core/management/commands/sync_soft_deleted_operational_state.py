from django.apps import apps
from django.core.management.base import BaseCommand, CommandError

from core.soft_delete.state_sync import (
    get_soft_deleted_rows_pending_state_sync,
    iter_soft_delete_models_with_operational_updates,
)


class Command(BaseCommand):
    help = "Sincroniza el estado operativo de registros soft-deleted previos al fix."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Detecta registros pendientes sin persistir cambios.",
        )
        parser.add_argument(
            "--app-label",
            type=str,
            help="Filtra por app label.",
        )
        parser.add_argument(
            "--model",
            type=str,
            help="Filtra por nombre de modelo. Requiere --app-label.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        app_label = options["app_label"]
        model_name = options["model"]

        if model_name and not app_label:
            raise CommandError("--model requiere --app-label.")

        if app_label:
            try:
                app_config = apps.get_app_config(app_label)
            except LookupError as exc:
                raise CommandError(f"App desconocida: {app_label}.") from exc
            app_label = app_config.label

        if model_name and app_label:
            try:
                apps.get_app_config(app_label).get_model(model_name)
            except LookupError as exc:
                raise CommandError(
                    f"Modelo desconocido: {app_label}.{model_name}."
                ) from exc

        total = 0
        for model, updates in iter_soft_delete_models_with_operational_updates(
            app_label=app_label,
            model_name=model_name,
        ):
            queryset = get_soft_deleted_rows_pending_state_sync(model, updates)
            count = queryset.count()
            if count == 0:
                continue

            total += count
            label = f"{model._meta.app_label}.{model.__name__}"
            self.stdout.write(f"{label}: {count} registro(s) -> {updates}")

            if not dry_run:
                queryset.update(**updates)

        action = "Detectados" if dry_run else "Sincronizados"
        self.stdout.write(f"{action}: {total} registro(s).")
