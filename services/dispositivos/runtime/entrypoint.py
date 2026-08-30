"""Ejecuta roles separados para el runtime de Dispositivos."""

import logging
import os
import subprocess
import sys
import time


logger = logging.getLogger("dispositivos.runtime")
WEB_ROLE = "web"
MIGRATE_ROLE = "migrate"
SETTINGS_MODULE = "services.dispositivos.runtime.settings"


def configure_django() -> None:
    """Selecciona los settings del servicio antes de cargar Django."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", SETTINGS_MODULE)


def database_wait_attempts() -> int:
    raw_attempts = os.getenv("DISPOSITIVOS_DB_WAIT_ATTEMPTS", "12")
    try:
        attempts = int(raw_attempts)
    except ValueError as exc:
        raise ValueError("DISPOSITIVOS_DB_WAIT_ATTEMPTS debe ser entero") from exc
    if attempts < 1:
        raise ValueError("DISPOSITIVOS_DB_WAIT_ATTEMPTS debe ser mayor que cero")
    return attempts


def wait_for_database() -> None:
    """Espera una conexión usable, con límite para no bloquear el despliegue."""
    configure_django()
    from django.db import connections  # pylint: disable=import-outside-toplevel

    attempts = database_wait_attempts()
    for attempt in range(1, attempts + 1):
        try:
            connection = connections["default"]
            connection.ensure_connection()
            connection.close()
            logger.info("[ok] Base de datos disponible.")
            return
        except Exception as exc:  # pragma: no cover - depende del driver/DB
            if attempt == attempts:
                raise RuntimeError("Base de datos no disponible") from exc
            logger.info(
                "[wait] Base de datos no disponible (%s/%s).", attempt, attempts
            )
            time.sleep(5)


def execute_django_command(arguments: list[str]) -> None:
    """Ejecuta un comando de Django con los settings de Dispositivos."""
    configure_django()
    from django.core.management import (  # pylint: disable=import-outside-toplevel
        execute_from_command_line,
    )

    execute_from_command_line(["dispositivos", *arguments])


def run_migrations() -> None:
    """Aplica sólo las migraciones de Dispositivos de forma idempotente."""
    wait_for_database()
    execute_django_command(["migrate", "dispositivos", "--noinput"])


def gunicorn_command() -> list[str]:
    """Construye el comando web sin incluir tareas de preparación o migración."""
    command = [
        "gunicorn",
        "services.dispositivos.runtime.wsgi:application",
        "--bind",
        f"0.0.0.0:{os.getenv('DISPOSITIVOS_WEB_PORT', '8000')}",
        "--workers",
        os.getenv("GUNICORN_WORKERS", "4"),
        "--log-level",
        "info",
    ]
    threads = os.getenv("GUNICORN_THREADS", "1")
    if threads != "1":
        command.extend(["--threads", threads])
    return command


def run_web() -> None:
    """Inicia únicamente el proceso web del servicio."""
    wait_for_database()
    subprocess.run(gunicorn_command(), check=True)


def main(arguments: list[str] | None = None) -> None:
    """Despacha un único rol explícito: ``web`` o ``migrate``."""
    role_arguments = arguments if arguments is not None else sys.argv[1:]
    role = role_arguments[0] if role_arguments else WEB_ROLE
    if role == WEB_ROLE:
        run_web()
        return
    if role == MIGRATE_ROLE:
        run_migrations()
        return
    raise ValueError(f"Rol de Dispositivos no soportado: {role}")


if __name__ == "__main__":
    main()
