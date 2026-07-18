"""Reusable importer for the PNUD collaborators data migration."""

from __future__ import annotations

import csv
import logging
from collections.abc import Iterable
from datetime import date

from django.db import DEFAULT_DB_ALIAS, transaction
from django.utils import timezone


PNUD_PROGRAMA_IDS = frozenset((3, 4))
BATCH_SIZE = 1000

# The seeded catalog stores this label with accents, while the supplied CSV does
# not. Keep the compatibility local to this one-off import.
ACTIVIDAD_CSV_ALIASES = {
    "Cuidado Ninos/Ninas/Adolesc": "Cuidado Niños/Niñas/Adolesc",
}


def _chunks(items: list, size: int = BATCH_SIZE) -> Iterable[list]:
    for start in range(0, len(items), size):
        yield items[start : start + size]


def _parse_csv(csv_path, logger):
    rows = []
    failed_rows = 0

    with open(csv_path, encoding="utf-8-sig", newline="") as csv_file:
        for row_number, raw_row in enumerate(csv.DictReader(csv_file), start=2):
            try:
                comedor_id = int((raw_row.get("ID Comedor") or "").strip())
                dni = int((raw_row.get("DNI") or "").strip())
                if comedor_id <= 0 or dni <= 0:
                    raise ValueError("ID Comedor y DNI deben ser positivos")
                fecha_alta = date.fromisoformat(
                    (raw_row.get("Fecha de Alta") or "").strip()
                )
            except (TypeError, ValueError) as exc:
                failed_rows += 1
                logger.warning(
                    "Fila %s omitida en colaboradores PNUD: %s", row_number, exc
                )
                continue

            telefono = (raw_row.get("Telefono") or "").strip()
            if not telefono:
                codigo_telefono = numero_telefono = None
            elif "-" in telefono:
                codigo_telefono, numero_telefono = (
                    value.strip() for value in telefono.split("-", 1)
                )
                codigo_telefono = codigo_telefono[:10]
                numero_telefono = numero_telefono[:20]
            else:
                codigo_telefono = None
                numero_telefono = telefono[:20]

            rows.append(
                {
                    "comedor_id": comedor_id,
                    "apellido": (raw_row.get("Apellido") or "").strip(),
                    "nombre": (raw_row.get("Nombre") or "").strip(),
                    "dni": dni,
                    "genero": {
                        "Mujer": "M",
                        "Varon": "V",
                        "Varón": "V",
                        "Mujer Travesti": "MT",
                        "Travesti": "TR",
                    }.get((raw_row.get("Genero") or "").strip(), "ND"),
                    "codigo_telefono": codigo_telefono,
                    "numero_telefono": numero_telefono,
                    "fecha_alta": fecha_alta,
                    "actividad": (raw_row.get("Actividades") or "").strip().replace(
                        ";", "/"
                    ),
                }
            )

    return rows, failed_rows


def _write_audit_best_effort(audit_model, entries, database, logger):
    if not audit_model or not entries:
        return

    try:
        with transaction.atomic(using=database):
            for batch in _chunks(entries):
                audit_model.objects.using(database).bulk_create(batch, batch_size=BATCH_SIZE)
    except Exception:  # pragma: no cover - depends on historical audit schema
        logger.exception("No se pudo registrar la auditoría PNUD de colaboradores.")


def replace_pnud_colaboradores(
    *, apps, csv_path, schema_editor=None, run_date=None, logger=None
):
    """Replace active PNUD collaborators from ``csv_path`` using historical models."""
    logger = logger or logging.getLogger(__name__)
    database = (
        schema_editor.connection.alias if schema_editor is not None else DEFAULT_DB_ALIAS
    )
    run_date = run_date or timezone.now().date()

    ColaboradorEspacio = apps.get_model("comedores", "ColaboradorEspacio")
    Ciudadano = apps.get_model("ciudadanos", "Ciudadano")
    ActividadColaboradorEspacio = apps.get_model(
        "comedores", "ActividadColaboradorEspacio"
    )
    Comedor = apps.get_model("comedores", "Comedor")
    try:
        AuditColaboradorEspacio = apps.get_model(
            "comedores", "AuditColaboradorEspacio"
        )
    except LookupError:
        AuditColaboradorEspacio = None

    rows, failed_rows = _parse_csv(csv_path, logger)
    stats = {
        "comedores_procesados": 0,
        "comedores_saltados_inexistentes": 0,
        "comedores_saltados_programa": 0,
        "colaboradores_soft_deleteados": 0,
        "colaboradores_creados": 0,
        "ciudadanos_creados": 0,
        "ciudadanos_reutilizados": 0,
        "filas_fallidas": failed_rows,
    }
    csv_comedor_ids = {row["comedor_id"] for row in rows}
    comedores = {
        comedor.id: comedor
        for comedor in Comedor.objects.using(database).filter(pk__in=csv_comedor_ids)
    }
    stats["comedores_saltados_inexistentes"] = len(csv_comedor_ids - comedores.keys())
    allowed_comedor_ids = {
        comedor_id
        for comedor_id, comedor in comedores.items()
        if comedor.programa_id in PNUD_PROGRAMA_IDS
    }
    stats["comedores_saltados_programa"] = len(
        set(comedores) - allowed_comedor_ids
    )
    rows = [row for row in rows if row["comedor_id"] in allowed_comedor_ids]
    stats["comedores_procesados"] = len(allowed_comedor_ids)

    if not rows:
        logger.info("Migración PNUD de colaboradores finalizada: %s", stats)
        return stats

    with transaction.atomic(using=database):
        dni_to_row = {row["dni"]: row for row in rows}
        ciudadano_by_dni = {}
        for ciudadano in (
            Ciudadano.objects.using(database)
            .filter(tipo_documento="DNI", documento__in=dni_to_row)
            .order_by("documento", "id")
            .iterator()
        ):
            if ciudadano.documento in ciudadano_by_dni:
                logger.warning(
                    "Múltiples ciudadanos activos para DNI %s; se usa el menor id.",
                    ciudadano.documento,
                )
                continue
            ciudadano_by_dni[ciudadano.documento] = ciudadano

        missing_dnis = set(dni_to_row) - set(ciudadano_by_dni)
        stats["ciudadanos_reutilizados"] = len(ciudadano_by_dni)
        stats["ciudadanos_creados"] = len(missing_dnis)
        new_ciudadanos = [
            Ciudadano(
                apellido=dni_to_row[dni]["apellido"],
                nombre=dni_to_row[dni]["nombre"],
                documento=dni,
                tipo_documento="DNI",
                sexo_id=None,
            )
            for dni in missing_dnis
        ]
        for batch in _chunks(new_ciudadanos):
            Ciudadano.objects.using(database).bulk_create(batch, batch_size=BATCH_SIZE)
        if missing_dnis:
            for ciudadano in (
                Ciudadano.objects.using(database)
                .filter(tipo_documento="DNI", documento__in=missing_dnis)
                .order_by("documento", "id")
            ):
                ciudadano_by_dni.setdefault(ciudadano.documento, ciudadano)

        activity_by_name = {
            activity.nombre: activity.id
            for activity in ActividadColaboradorEspacio.objects.using(database).all()
        }
        for row in rows:
            if not row["actividad"]:
                row["actividad_id"] = None
                continue
            activity_name = ACTIVIDAD_CSV_ALIASES.get(
                row["actividad"], row["actividad"]
            )
            row["actividad_id"] = activity_by_name.get(activity_name)
            if row["actividad_id"] is None:
                logger.warning(
                    "Actividad PNUD no encontrada para DNI %s: %s",
                    row["dni"],
                    row["actividad"],
                )

        old_collaborators = list(
            ColaboradorEspacio.objects.using(database)
            .filter(comedor_id__in=allowed_comedor_ids, fecha_baja__isnull=True)
            .values("id", "comedor_id", "ciudadano_id", "genero", "fecha_alta")
        )
        stats["colaboradores_soft_deleteados"] = len(old_collaborators)
        ColaboradorEspacio.objects.using(database).filter(
            comedor_id__in=allowed_comedor_ids, fecha_baja__isnull=True
        ).update(fecha_baja=run_date)

        _write_audit_best_effort(
            AuditColaboradorEspacio,
            [
                AuditColaboradorEspacio(
                    colaborador_id=old["id"],
                    comedor_id=old["comedor_id"],
                    ciudadano_id=old["ciudadano_id"],
                    changed_by_id=None,
                    accion="delete",
                    snapshot_antes={
                        "id": old["id"],
                        "genero": old["genero"],
                        "fecha_alta": old["fecha_alta"].isoformat(),
                        "fecha_baja": None,
                    },
                    snapshot_despues={
                        "id": old["id"],
                        "fecha_baja": run_date.isoformat(),
                    },
                    metadata={"source": "pnud_csv_2099"},
                )
                for old in old_collaborators
            ]
            if AuditColaboradorEspacio
            else [],
            database,
            logger,
        )

        new_collaborators = [
            ColaboradorEspacio(
                comedor_id=row["comedor_id"],
                ciudadano_id=ciudadano_by_dni[row["dni"]].id,
                genero=row["genero"],
                codigo_telefono=row["codigo_telefono"],
                numero_telefono=row["numero_telefono"],
                fecha_alta=row["fecha_alta"],
                fecha_baja=None,
                creado_por_id=None,
                modificado_por_id=None,
            )
            for row in rows
        ]
        for batch in _chunks(new_collaborators):
            ColaboradorEspacio.objects.using(database).bulk_create(
                batch, batch_size=BATCH_SIZE
            )
        stats["colaboradores_creados"] = len(new_collaborators)

        created_by_key = {
            (colaborador.comedor_id, colaborador.ciudadano_id): colaborador
            for colaborador in ColaboradorEspacio.objects.using(database).filter(
                comedor_id__in=allowed_comedor_ids,
                fecha_baja__isnull=True,
            )
        }
        for row in rows:
            key = (row["comedor_id"], ciudadano_by_dni[row["dni"]].id)
            if key not in created_by_key:
                raise RuntimeError(
                    "No se pudo recuperar el colaborador PNUD recién creado."
                )

        activity_field = ColaboradorEspacio._meta.get_field("actividades")
        through_model = activity_field.remote_field.through
        collaborator_field = activity_field.m2m_field_name()
        activity_field_name = activity_field.m2m_reverse_field_name()
        through_rows = [
            through_model(
                **{
                    f"{collaborator_field}_id": created_by_key[
                        (row["comedor_id"], ciudadano_by_dni[row["dni"]].id)
                    ].id,
                    f"{activity_field_name}_id": row["actividad_id"],
                }
            )
            for row in rows
            if row["actividad_id"] is not None
        ]
        for batch in _chunks(through_rows):
            through_model.objects.using(database).bulk_create(
                batch, batch_size=BATCH_SIZE
            )

        _write_audit_best_effort(
            AuditColaboradorEspacio,
            [
                AuditColaboradorEspacio(
                    colaborador_id=created_by_key[
                        (row["comedor_id"], ciudadano_by_dni[row["dni"]].id)
                    ].id,
                    comedor_id=row["comedor_id"],
                    ciudadano_id=ciudadano_by_dni[row["dni"]].id,
                    changed_by_id=None,
                    accion="create",
                    snapshot_despues={
                        "genero": row["genero"],
                        "fecha_alta": row["fecha_alta"].isoformat(),
                        "fecha_baja": None,
                    },
                    metadata={"source": "pnud_csv_2099"},
                )
                for row in rows
            ]
            if AuditColaboradorEspacio
            else [],
            database,
            logger,
        )

    logger.info("Migración PNUD de colaboradores finalizada: %s", stats)
    return stats
