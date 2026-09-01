"""Audita y repara mojibake reversible en campos de identidad seleccionados."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field

from django.apps import apps
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from core.services.text_encoding import (
    contains_mojibake_marker,
    repair_utf8_mojibake,
)


DEFAULT_BATCH_SIZE = 2000
TARGETS = {
    "ciudadano": ("ciudadanos", "Ciudadano", ("apellido", "nombre")),
    "nomina_cdi": (
        "centrodeinfancia",
        "NominaCentroInfancia",
        ("apellido", "nombre"),
    ),
}


@dataclass
class TargetStats:
    scanned: int = 0
    changed_rows: int = 0
    changed_fields: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    unresolved_fields: dict[str, int] = field(default_factory=lambda: defaultdict(int))


def _model_manager(model):
    if hasattr(model, "all_objects"):
        return model.all_objects
    return model._default_manager  # pylint: disable=protected-access


def _repair_objects(objects, fields):
    updates_by_fieldset = defaultdict(list)
    stats = TargetStats(scanned=len(objects))

    for instance in objects:
        changed = []
        for field_name in fields:
            original = getattr(instance, field_name)
            if not isinstance(original, str) or not original:
                continue

            repaired = repair_utf8_mojibake(original)
            if repaired != original:
                setattr(instance, field_name, repaired)
                changed.append(field_name)
                stats.changed_fields[field_name] += 1

            if contains_mojibake_marker(repaired):
                stats.unresolved_fields[field_name] += 1

        if changed:
            stats.changed_rows += 1
            updates_by_fieldset[tuple(changed)].append(instance)

    return updates_by_fieldset, stats


class Command(BaseCommand):
    help = (
        "Audita mojibake reversible en nombres y apellidos; "
        "sólo escribe con --apply."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Aplica los cambios detectados. Sin esta opción sólo informa conteos.",
        )
        parser.add_argument(
            "--target",
            action="append",
            choices=tuple(TARGETS),
            help="Limita la ejecución a uno o más targets.",
        )
        parser.add_argument(
            "--field",
            action="append",
            choices=("apellido", "nombre"),
            help="Limita la ejecución a uno o más campos.",
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=DEFAULT_BATCH_SIZE,
            dest="batch_size",
            help=f"Filas por lote (default: {DEFAULT_BATCH_SIZE}).",
        )

    def handle(self, *args, **options):
        apply_changes = options["apply"]
        batch_size = options["batch_size"]
        if batch_size <= 0:
            raise CommandError("--batch-size debe ser mayor que cero.")

        target_names = list(dict.fromkeys(options["target"] or TARGETS))
        requested_fields = set(options["field"] or ())

        mode = "APPLY" if apply_changes else "DRY-RUN"
        self.stdout.write(f"=== Reparación UTF-8 mojibake: {mode} ===")
        if not apply_changes:
            self.stdout.write("No se realizarán escrituras en la base de datos.")

        totals = TargetStats()
        for target_name in target_names:
            target = TARGETS[target_name]
            model = apps.get_model(*target[:2])
            available_fields = target[2]
            fields = tuple(
                field_name
                for field_name in available_fields
                if not requested_fields or field_name in requested_fields
            )
            target_stats = self._process_target(
                model=model,
                fields=fields,
                batch_size=batch_size,
                apply_changes=apply_changes,
            )
            self._merge_stats(totals, target_stats)
            self._write_stats(target_name, fields, target_stats)

        self.stdout.write(
            self.style.SUCCESS(
                "Total: "
                f"{totals.scanned} filas revisadas, "
                f"{totals.changed_rows} filas con cambios reversibles."
            )
        )

    def _process_target(self, *, model, fields, batch_size, apply_changes):
        manager = _model_manager(model)
        stats = TargetStats()
        last_pk = 0

        while True:
            primary_keys = list(
                manager.filter(pk__gt=last_pk)
                .order_by("pk")
                .values_list("pk", flat=True)[:batch_size]
            )
            if not primary_keys:
                break

            if apply_changes:
                with transaction.atomic(using=manager.db):
                    objects = list(
                        manager.select_for_update()
                        .filter(pk__in=primary_keys)
                        .only("pk", *fields)
                        .order_by("pk")
                    )
                    updates, batch_stats = _repair_objects(objects, fields)
                    for changed_fields, changed_objects in updates.items():
                        manager.bulk_update(
                            changed_objects,
                            fields=changed_fields,
                            batch_size=batch_size,
                        )
            else:
                objects = list(
                    manager.filter(pk__in=primary_keys)
                    .only("pk", *fields)
                    .order_by("pk")
                )
                _, batch_stats = _repair_objects(objects, fields)

            self._merge_stats(stats, batch_stats)
            last_pk = primary_keys[-1]

        return stats

    @staticmethod
    def _merge_stats(destination, source):
        destination.scanned += source.scanned
        destination.changed_rows += source.changed_rows
        for field_name, count in source.changed_fields.items():
            destination.changed_fields[field_name] += count
        for field_name, count in source.unresolved_fields.items():
            destination.unresolved_fields[field_name] += count

    def _write_stats(self, target_name, fields, stats):
        self.stdout.write(
            f"{target_name}: {stats.scanned} filas revisadas; "
            f"{stats.changed_rows} filas con cambios reversibles."
        )
        for field_name in fields:
            self.stdout.write(
                f"  {field_name}: "
                f"{stats.changed_fields[field_name]} cambios; "
                f"{stats.unresolved_fields[field_name]} marcadores pendientes."
            )
