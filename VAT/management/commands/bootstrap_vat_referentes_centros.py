from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError

from VAT.management.commands import import_vat_centros_excel as centros_import
from VAT.models import Centro
from core.models import Localidad, Municipio, Provincia
from users.management.commands import import_vat_cfp_users as users_import


@dataclass(frozen=True)
class PlannedUserAssignment:
    line_number: int
    username: str
    display_name: str


@dataclass(frozen=True)
class PlannedCenterAssignment:
    line_number: int
    codigo: str
    nombre: str


def _plan_user_rows(
    *,
    file_path: Path,
    sheet_name: str | None,
    default_password: str,
) -> list[PlannedUserAssignment]:
    headers, raw_rows = users_import.load_rows(file_path, sheet_name)
    header_mapping = users_import.resolve_header_mapping(headers)

    planned_rows: list[PlannedUserAssignment] = []
    batch_usernames: set[str] = set()
    user_model = get_user_model()

    for line_number, raw_values in raw_rows:
        if not any(raw_values):
            continue

        parsed_row = users_import.build_parsed_row(
            line_number=line_number,
            raw_values=raw_values,
            header_mapping=header_mapping,
            default_password=default_password,
        )

        username = parsed_row.username
        if not username:
            username = users_import.resolve_generated_username(
                parsed_row=parsed_row,
                batch_usernames=batch_usernames,
                user_model=user_model,
            )
        else:
            batch_usernames.add(username)

        planned_rows.append(
            PlannedUserAssignment(
                line_number=line_number,
                username=username,
                display_name=parsed_row.display_name,
            )
        )

    return planned_rows


def _plan_center_rows(
    *,
    file_path: Path,
    sheet_name: str | None,
) -> list[PlannedCenterAssignment]:
    headers, raw_rows = centros_import.load_rows(file_path, sheet_name)
    header_mapping = centros_import.resolve_header_mapping(headers)

    planned_rows: list[PlannedCenterAssignment] = []

    for line_number, raw_values in raw_rows:
        if not any(raw_values):
            continue

        parsed_row = centros_import.build_parsed_row(
            line_number=line_number,
            raw_values=raw_values,
            header_mapping=header_mapping,
        )

        # Valida referencias geográficas y referente explícito si viniera en la planilla.
        centros_import.resolve_foreign_keys(parsed_row)

        planned_rows.append(
            PlannedCenterAssignment(
                line_number=line_number,
                codigo=parsed_row.codigo,
                nombre=parsed_row.nombre,
            )
        )

    return planned_rows


class Command(BaseCommand):
    help = (
        "Ejecuta el alta masiva completa de VAT: usuarios CFP, centros y asignación "
        "de referentes por orden de fila."
    )

    def add_arguments(self, parser):
        parser.add_argument("users_file", type=str)
        parser.add_argument("centers_file", type=str)
        parser.add_argument("--default-password", type=str, default="")
        parser.add_argument("--users-sheet-name", type=str, default=None)
        parser.add_argument("--centers-sheet-name", type=str, default=None)
        parser.add_argument("--dry-run", action="store_true")
        parser.add_argument("--overwrite", action="store_true")

    def handle(self, *args, **options):
        users_file = Path(options["users_file"])
        centers_file = Path(options["centers_file"])
        default_password = (options.get("default_password") or "").strip()
        users_sheet_name = options.get("users_sheet_name")
        centers_sheet_name = options.get("centers_sheet_name")
        dry_run = options["dry_run"]
        overwrite = options["overwrite"]

        if not users_file.exists():
            raise CommandError(f"El archivo de usuarios '{users_file}' no existe.")
        if not centers_file.exists():
            raise CommandError(f"El archivo de centros '{centers_file}' no existe.")

        if not default_password:
            raise CommandError("Debe indicar --default-password para el alta masiva.")

        try:
            planned_users = _plan_user_rows(
                file_path=users_file,
                sheet_name=users_sheet_name,
                default_password=default_password,
            )
            planned_centers = _plan_center_rows(
                file_path=centers_file,
                sheet_name=centers_sheet_name,
            )
        except ValueError as exc:
            raise CommandError(str(exc)) from exc

        if len(planned_users) != len(planned_centers):
            raise CommandError(
                "La cantidad de filas válidas de usuarios y centros no coincide: "
                f"usuarios={len(planned_users)}, centros={len(planned_centers)}."
            )

        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    "Simulación finalizada. "
                    f"Usuarios planificados: {len(planned_users)}, "
                    f"centros planificados: {len(planned_centers)}, "
                    f"asignaciones proyectadas: {len(planned_users)}."
                )
            )
            return

        self.stdout.write("1/3 Importando usuarios CFP...")
        call_command(
            "import_vat_cfp_users",
            str(users_file),
            f"--default-password={default_password}",
            *(
                [f"--sheet-name={users_sheet_name}"]
                if users_sheet_name
                else []
            ),
        )

        self.stdout.write("2/3 Importando centros VAT...")
        call_command(
            "import_vat_centros_excel",
            str(centers_file),
            *(
                [f"--sheet-name={centers_sheet_name}"]
                if centers_sheet_name
                else []
            ),
        )

        self.stdout.write("3/3 Asignando referentes a centros...")
        assigned_count = 0
        skipped_existing_count = 0

        for planned_user, planned_center in zip(planned_users, planned_centers):
            user = get_user_model().objects.filter(username=planned_user.username).first()
            if user is None:
                raise CommandError(
                    f"No se encontró el usuario '{planned_user.username}' para la fila {planned_user.line_number}."
                )

            center = Centro.objects.filter(codigo=planned_center.codigo).first()
            if center is None:
                raise CommandError(
                    f"No se encontró el centro '{planned_center.codigo}' para la fila {planned_center.line_number}."
                )

            if center.referente_id and center.referente_id != user.id and not overwrite:
                skipped_existing_count += 1
                self.stdout.write(
                    self.style.WARNING(
                        f"Centro {center.codigo} ya tiene referente asignado; se omite."
                    )
                )
                continue

            if center.referente_id == user.id:
                continue

            center.referente = user
            center.save(update_fields=["referente"])
            assigned_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                "Proceso finalizado. "
                f"Usuarios planificados: {len(planned_users)}, "
                f"centros planificados: {len(planned_centers)}, "
                f"referentes asignados: {assigned_count}, "
                f"centros omitidos por referente existente: {skipped_existing_count}."
            )
        )