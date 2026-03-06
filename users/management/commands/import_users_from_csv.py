import csv
from datetime import timedelta
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from users.models import Profile


class Command(BaseCommand):
    """Create or update users from a CSV and copy groups from a reference user."""

    help = "Crea usuarios a partir de un CSV y replica los grupos del usuario de referencia."

    def add_arguments(self, parser):
        parser.add_argument(
            "csv_path",
            type=str,
            help="Ruta al archivo CSV con las columnas requeridas.",
        )
        parser.add_argument(
            "--reference-user-id",
            type=int,
            default=368,
            help="ID del usuario cuyos grupos se copiarán (por defecto 368).",
        )

    def handle(self, *args, **options):
        csv_path = Path(options["csv_path"])
        reference_user_id = options["reference_user_id"]

        if not csv_path.exists():
            raise CommandError(f"El archivo '{csv_path}' no existe.")

        user_model = get_user_model()

        try:
            reference_user = user_model.objects.get(pk=reference_user_id)
        except user_model.DoesNotExist as exc:
            raise CommandError(
                f"No se encontró el usuario de referencia con id={reference_user_id}."
            ) from exc

        reference_groups = list(reference_user.groups.all())

        created_count = 0
        updated_count = 0

        with csv_path.open(newline="", encoding="utf-8-sig") as csv_file:
            reader = csv.DictReader(csv_file)
            expected_columns = {
                "Usuario",
                "Email",
                "Nombre completo",
                "Apellido",
                "Rol",
                "Contraseña",
            }
            headers = set(reader.fieldnames or [])
            missing_columns = expected_columns - headers
            if missing_columns:
                missing = ", ".join(sorted(missing_columns))
                raise CommandError(
                    f"El CSV no contiene las columnas requeridas: {missing}"
                )

            for line_number, row in enumerate(reader, start=2):
                username = (row.get("Usuario") or "").strip()
                if not username:
                    self.stdout.write(
                        self.style.WARNING(
                            "Se encontró una fila sin valor en 'Usuario'; se omite."
                        )
                    )
                    continue

                email = (row.get("Email") or "").strip()
                if not email:
                    raise CommandError(
                        f"Fila {line_number}: el campo 'Email' es obligatorio para crear o actualizar usuarios."
                    )
                first_name = (row.get("Nombre completo") or "").strip()
                last_name = (row.get("Apellido") or "").strip()
                rol = (row.get("Rol") or "").strip()
                raw_password = (row.get("Contraseña") or "").strip()

                user, created = user_model.objects.get_or_create(
                    username=username, defaults={"email": email}
                )
                if created:
                    created_count += 1
                else:
                    updated_count += 1
                    if email:
                        user.email = email

                user.first_name = first_name
                user.last_name = last_name
                if raw_password:
                    user.set_password(raw_password)
                user.save()

                profile, _ = Profile.objects.get_or_create(user=user)
                profile.rol = rol
                if raw_password:
                    profile.must_change_password = True
                    profile.password_changed_at = None
                    profile.initial_password_expires_at = timezone.now() + timedelta(
                        hours=settings.INITIAL_PASSWORD_MAX_AGE_HOURS
                    )
                    profile.save(
                        update_fields=[
                            "rol",
                            "must_change_password",
                            "password_changed_at",
                            "initial_password_expires_at",
                        ]
                    )
                else:
                    profile.save(update_fields=["rol"])

                user.groups.set(reference_groups)

                action = "creado" if created else "actualizado"
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Usuario '{username}' {action} y grupos replicados."
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"Proceso finalizado. Usuarios creados: {created_count}, actualizados: {updated_count}."
            )
        )
