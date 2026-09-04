"""Audita campos de texto explícitos sin exponer sus valores."""

from django.apps import apps
from django.core.exceptions import FieldDoesNotExist
from django.core.management.base import BaseCommand, CommandError
from django.db import models

from core.services.text_encoding import (
    contains_mojibake_marker,
    repair_utf8_mojibake,
)


DEFAULT_BATCH_SIZE = 5000


def _resolve_field(spec):
    try:
        app_label, model_name, field_name = spec.split(".", maxsplit=2)
    except ValueError as exc:
        raise CommandError(f"Campo inválido {spec!r}; use app.Model.campo.") from exc

    model = apps.get_model(app_label, model_name)
    if model is None:
        raise CommandError(f"No existe el modelo {app_label}.{model_name}.")
    try:
        model_field = model._meta.get_field(field_name)
    except FieldDoesNotExist as exc:
        raise CommandError(f"No existe el campo {spec}.") from exc
    if not isinstance(model_field, (models.CharField, models.TextField)):
        raise CommandError(f"El campo {spec} no es CharField ni TextField.")
    return model, field_name


class Command(BaseCommand):
    help = "Audita campos de texto explícitos buscando mojibake reversible."

    def add_arguments(self, parser):
        parser.add_argument(
            "--field",
            action="append",
            required=True,
            help="Campo app.Model.campo. Puede repetirse.",
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=DEFAULT_BATCH_SIZE,
            dest="batch_size",
            help=f"Filas leídas por lote (default: {DEFAULT_BATCH_SIZE}).",
        )

    def handle(self, *args, **options):
        batch_size = options["batch_size"]
        if batch_size <= 0:
            raise CommandError("--batch-size debe ser mayor que cero.")

        field_specs = list(dict.fromkeys(options["field"]))
        self.stdout.write("=== Auditoría UTF-8 mojibake (sólo lectura) ===")
        for spec in field_specs:
            self._audit_field(spec, batch_size)

    def _audit_field(self, spec, batch_size):
        model, field_name = _resolve_field(spec)
        if hasattr(model, "all_objects"):
            manager = model.all_objects
        else:
            manager = model._default_manager  # pylint: disable=protected-access
        scanned = 0
        repairable = 0
        unresolved = 0

        queryset = (
            manager.order_by("pk")
            .only("pk", field_name)
            .iterator(chunk_size=batch_size)
        )
        for instance in queryset:
            scanned += 1
            original = getattr(instance, field_name)
            if not isinstance(original, str) or not original:
                continue
            repaired = repair_utf8_mojibake(original)
            if repaired != original:
                repairable += 1
            if contains_mojibake_marker(repaired):
                unresolved += 1

        self.stdout.write(
            f"{spec}: {scanned} filas; "
            f"{repairable} reparables; {unresolved} marcadores pendientes."
        )
