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
DEPLOY_GUNICORN_ENVIRONMENTS = {"qa", "homologacion", "prd"}


def run_command(cmd, *, stage, **kwargs):
    """
    Ejecuta un comando y falla explÃƒÂ­citamente si el exit code es distinto de cero.
    """
    logger.info("Ã¢â€“Â¶ %s: %s", stage, " ".join(cmd))
    try:
        return subprocess.run(cmd, check=True, **kwargs)
    except subprocess.CalledProcessError as exc:
        logger.error(
            "Ã¢ÂÅ’ FallÃƒÂ³ %s (exit=%s): %s", stage, exc.returncode, " ".join(cmd)
        )
        raise


def wait_for_mysql():
    """
    Espera a que MySQL estÃƒÂ© disponible antes de continuar.
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
            "Ã¢ÂÅ’ Error: Faltan variables de entorno para la conexiÃƒÂ³n a la base de datos"
        )
        logger.error(
            "   AsegÃƒÂºrese de definir DATABASE_HOST, DATABASE_USER y DATABASE_PASSWORD"
        )
        return

    logger.info("Ã¢ÂÂ³ Esperando que MySQL estÃƒÂ© disponible...")
    while True:
        try:
            conn = pymysql.connect(host=host, port=port, user=user, password=password)
            conn.close()
            break
        except pymysql.MySQLError:
            time.sleep(5)
    time.sleep(10)
    logger.info("Ã¢Å“â€¦ MySQL estÃƒÂ¡ listo.")


def run_django_commands():
    """
    Ejecuta los comandos de Django necesarios para la preparaciÃƒÂ³n y el funcionamiento de la aplicaciÃƒÂ³n.
    """
    environment = os.getenv("ENVIRONMENT", "dev").lower()
    run_makemigrations_on_start = (
        os.getenv(
            "RUN_MAKEMIGRATIONS_ON_START",
            "true" if environment == "dev" else "false",
        ).lower()
        == "true"
    )

    if run_makemigrations_on_start:
        run_command(
            ["python", "manage.py", "makemigrations"],
            stage="makemigrations",
        )
    else:
        logger.info("Ã¢ÂÂ­ Omitiendo makemigrations en arranque (flag desactivado).")

    run_command(["python", "manage.py", "migrate", "auth"], stage="migrate auth")
    run_command(["python", "manage.py", "migrate", "--noinput"], stage="migrate")

    # Cargar los fixtures condicionalmente, si se quiere forzar aÃƒÂ±adir `--force`
    run_command(["python", "manage.py", "load_fixtures"], stage="load_fixtures")

    run_command(
        ["python", "manage.py", "create_test_users"],
        stage="create_test_users",
    )
    run_command(["python", "manage.py", "create_groups"], stage="create_groups")
    run_server()


def run_server():
    """
    Inicia el servidor de Django. Usa Gunicorn en producciÃƒÂ³n o el servidor de desarrollo si no.
    """
    environment = os.getenv("ENVIRONMENT", "dev").lower()
    deploy_gunicorn = environment in DEPLOY_GUNICORN_ENVIRONMENTS

    if deploy_gunicorn:
        cache_busting()
        logger.info("Ã°Å¸Å¡â‚¬ Iniciando Django en modo producciÃƒÂ³n con Gunicorn...")
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
        logger.info("Ã°Å¸Â§Âª Iniciando Django en modo desarrollo...")
        run_command(
            ["python", "manage.py", "runserver", "0.0.0.0:8000"],
            stage="runserver",
        )


def cache_busting():
    static_root = (
        Path(__file__).resolve().parent.parent / "static_root"
    )  # RaÃƒÂ­z del proyecto
    if static_root.exists() and static_root.is_dir():
        logger.info("Ã°Å¸Â§Â¹ Eliminando carpeta de estÃƒÂ¡ticos: %s", static_root)
        shutil.rmtree(static_root)
    logger.info("Ã°Å¸â€œÂ¦ Ejecutando collectstatic para cache busting...")
    run_command(
        ["python", "manage.py", "collectstatic", "--noinput"],
        stage="collectstatic",
        stdout=subprocess.DEVNULL,
    )


if __name__ == "__main__":
    wait_for_mysql()
    run_django_commands()
