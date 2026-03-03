import logging
import os
import subprocess
import time
import shutil
from pathlib import Path

import pymysql


if not logging.getLogger().handlers:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("django")


def run_command(cmd, *, stage, **kwargs):
    """
    Ejecuta un comando y falla explícitamente si el exit code es distinto de cero.
    """
    logger.info("▶ %s: %s", stage, " ".join(cmd))
    try:
        return subprocess.run(cmd, check=True, **kwargs)
    except subprocess.CalledProcessError as exc:
        logger.error("❌ Falló %s (exit=%s): %s", stage, exc.returncode, " ".join(cmd))
        raise


def wait_for_mysql():
    """
    Espera a que MySQL esté disponible antes de continuar.
    Usa las variables de entorno DATABASE_HOST, DATABASE_PORT, DATABASE_USER y DATABASE_PASSWORD.
    Se puede omitir con la variable WAIT_FOR_DB=false.
    """
    host = os.getenv("DATABASE_HOST")
    port = int(os.getenv("DATABASE_PORT"))
    user = os.getenv("DATABASE_USER")
    password = os.getenv("DATABASE_PASSWORD")
    wait_for_db = os.getenv("WAIT_FOR_DB", "true").lower() == "true"

    if not wait_for_db:
        return

    if not all([host, user, password]):
        logger.error(
            "❌ Error: Faltan variables de entorno para la conexión a la base de datos"
        )
        logger.error(
            "   Asegúrese de definir DATABASE_HOST, DATABASE_USER y DATABASE_PASSWORD"
        )
        return

    logger.info("⏳ Esperando que MySQL esté disponible...")
    while True:
        try:
            conn = pymysql.connect(host=host, port=port, user=user, password=password)
            conn.close()
            break
        except pymysql.MySQLError:
            time.sleep(5)
    time.sleep(10)
    logger.info("✅ MySQL está listo.")


def run_django_commands():
    """
    Ejecuta los comandos de Django necesarios para la preparación y el funcionamiento de la aplicación.
    """
    environment = os.getenv("ENVIRONMENT", "dev").lower()
    run_makemigrations_on_start = (
        os.getenv(
            "RUN_MAKEMIGRATIONS_ON_START",
            "true" if environment == "dev" else "false",
        ).lower()
        == "true"
    )
    # Backward compat: también aceptar RUN_MAKEMIGRATIONS
    if not run_makemigrations_on_start:
        run_makemigrations_on_start = (
            os.getenv("RUN_MAKEMIGRATIONS", "").lower() == "true"
        )

    if run_makemigrations_on_start:
        run_command(
            ["python", "manage.py", "makemigrations"],
            stage="makemigrations",
        )
    else:
        logger.info("⏭ Omitiendo makemigrations en arranque (flag desactivado).")

    run_command(["python", "manage.py", "migrate", "auth"], stage="migrate auth")
    run_command(["python", "manage.py", "migrate", "--noinput"], stage="migrate")

    # Cargar los fixtures condicionalmente, si se quiere forzar añadir `--force`
    run_command(["python", "manage.py", "load_fixtures"], stage="load_fixtures")

    run_command(
        ["python", "manage.py", "create_test_users"],
        stage="create_test_users",
    )
    run_command(["python", "manage.py", "create_groups"], stage="create_groups")
    run_server()


def run_server():
    """
    Inicia el servidor de Django. Usa Gunicorn en producción o el servidor de desarrollo si no.
    """
    environment = os.getenv("ENVIRONMENT", "dev").lower()
    deploy_gunicorn = environment in ("prd", "qa")

    if deploy_gunicorn:
        cache_busting()
        logger.info("🚀 Iniciando Django en modo producción con Gunicorn...")
        workers = os.getenv("GUNICORN_WORKERS", "4")
        threads = os.getenv("GUNICORN_THREADS", "1")
        cmd = [
            "gunicorn",
            "config.wsgi:application",
            "-b",
            "0.0.0.0:8000",
            "--workers",
            workers,
            "--log-level",
            "info",
        ]
        if threads and threads != "1":
            cmd.extend(["--threads", threads])
        run_command(cmd, stage="gunicorn")
    else:
        logger.info("🧪 Iniciando Django en modo desarrollo...")
        run_command(
            ["python", "manage.py", "runserver", "0.0.0.0:8000"],
            stage="runserver",
        )


def cache_busting():
    static_root = (
        Path(__file__).resolve().parent.parent / "static_root"
    )  # Raíz del proyecto
    if static_root.exists() and static_root.is_dir():
        logger.info("🧹 Eliminando carpeta de estáticos: %s", static_root)
        shutil.rmtree(static_root)
    logger.info("📦 Ejecutando collectstatic para cache busting...")
    run_command(
        ["python", "manage.py", "collectstatic", "--noinput"],
        stage="collectstatic",
        stdout=subprocess.DEVNULL,
    )


if __name__ == "__main__":
    wait_for_mysql()
    run_django_commands()
