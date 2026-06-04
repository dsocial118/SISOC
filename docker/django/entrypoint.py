import logging
import os
import shutil
import subprocess
import time
from pathlib import Path

import pymysql


if not logging.getLogger().handlers:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("django")
DEPLOY_GUNICORN_ENVIRONMENTS = {"qa", "homologacion", "prd"}
SERVICE_ROLE_WEB = "web"
SERVICE_ROLE_BULK_CREDENTIALS_WORKER = "bulk_credentials_worker"
SERVICE_ROLE_CIUDADANOS_IMPORT_WORKER = "ciudadanos_import_worker"


def run_command(cmd, *, stage, **kwargs):
    """
    Ejecuta un comando y falla explicitamente si el exit code es distinto de cero.
    """
    logger.info("[run] %s: %s", stage, " ".join(cmd))
    try:
        return subprocess.run(cmd, check=True, **kwargs)
    except subprocess.CalledProcessError as exc:
        logger.error(
            "[error] Fallo %s (exit=%s): %s",
            stage,
            exc.returncode,
            " ".join(cmd),
        )
        raise


def wait_for_mysql():
    """
    Espera a que MySQL este disponible antes de continuar.
    Usa las variables de entorno DATABASE_HOST, DATABASE_PORT,
    DATABASE_USER y DATABASE_PASSWORD.
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
            (
                "[error] Faltan variables de entorno para "
                "la conexion a la base de datos"
            )
        )
        logger.error(
            (
                "   Asegurese de definir DATABASE_HOST, DATABASE_USER "
                "y DATABASE_PASSWORD"
            )
        )
        return

    logger.info("[wait] Esperando que MySQL este disponible...")
    while True:
        try:
            conn = pymysql.connect(
                host=host,
                port=port,
                user=user,
                password=password,
            )
            conn.close()
            break
        except pymysql.MySQLError:
            time.sleep(5)
    time.sleep(10)
    logger.info("[ok] MySQL esta listo.")


def fix_migration_history():
    """
    Registra ciudadanos.0028_merge_20260505_1126 en django_migrations si el
    registro fantasma 0028_merge_20260420_0000 existe pero la nueva versión no.
    Esto ocurre en DBs creadas antes de que se renombrara esa migración de merge.
    Corre antes de makemigrations para que check_consistent_history no falle.
    """
    host = os.getenv("DATABASE_HOST")
    port = int(os.getenv("DATABASE_PORT", "3306"))
    user = os.getenv("DATABASE_USER")
    password = os.getenv("DATABASE_PASSWORD")
    database = os.getenv("DATABASE_NAME")

    if not all([host, user, password, database]):
        return

    try:
        conn = pymysql.connect(
            host=host, port=port, user=user, password=password, database=database
        )
        with conn.cursor() as cur:
            cur.execute(
                "SELECT 1 FROM django_migrations " "WHERE app=%s AND name=%s",
                ("ciudadanos", "0028_merge_20260420_0000"),
            )
            has_ghost = cur.fetchone() is not None
            if not has_ghost:
                return
            cur.execute(
                "SELECT 1 FROM django_migrations " "WHERE app=%s AND name=%s",
                ("ciudadanos", "0028_merge_20260505_1126"),
            )
            already_recorded = cur.fetchone() is not None
            if already_recorded:
                return
            cur.execute(
                "INSERT INTO django_migrations (app, name, applied) "
                "VALUES (%s, %s, NOW())",
                ("ciudadanos", "0028_merge_20260505_1126"),
            )
            conn.commit()
            logger.info(
                "[fix] Registrado ciudadanos.0028_merge_20260505_1126 "
                "en django_migrations (migración fantasma resuelta)."
            )
    except Exception as exc:
        logger.warning("[fix] fix_migration_history: %s", exc)
    finally:
        try:
            conn.close()
        except Exception:
            pass


def run_django_commands():
    """
    Ejecuta los comandos de Django necesarios para la preparacion
    y el funcionamiento de la aplicacion.
    """
    environment = os.getenv("ENVIRONMENT", "dev").lower()
    run_makemigrations_on_start = (
        os.getenv(
            "RUN_MAKEMIGRATIONS_ON_START",
            "true" if environment == "dev" else "false",
        ).lower()
        == "true"
    )

    fix_migration_history()

    if run_makemigrations_on_start:
        run_command(
            ["python", "manage.py", "makemigrations"],
            stage="makemigrations",
        )
    else:
        logger.info("[skip] Omitiendo makemigrations en arranque (flag desactivado).")

    run_command(["python", "manage.py", "migrate", "auth"], stage="migrate auth")
    run_command(["python", "manage.py", "migrate", "--noinput"], stage="migrate")

    # Cargar los fixtures condicionalmente, si se quiere forzar anadir `--force`
    run_command(["python", "manage.py", "load_fixtures"], stage="load_fixtures")

    run_command(
        ["python", "manage.py", "create_test_users"],
        stage="create_test_users",
    )
    run_command(["python", "manage.py", "create_groups"], stage="create_groups")
    run_server()


def run_bulk_credentials_worker():
    """Inicia el worker dedicado de credenciales masivas."""
    logger.info("[worker] Iniciando worker de credenciales masivas...")
    run_command(
        ["python", "manage.py", "process_bulk_credentials_jobs"],
        stage="bulk_credentials_worker",
    )


def run_ciudadanos_import_worker():
    """Inicia el worker dedicado de importacion masiva de ciudadanos."""
    logger.info("[worker] Iniciando worker de importacion masiva de ciudadanos...")
    run_command(
        ["python", "manage.py", "process_ciudadanos_import_jobs"],
        stage="ciudadanos_import_worker",
    )


def main():
    wait_for_mysql()
    service_role = os.getenv("DJANGO_SERVICE_ROLE", SERVICE_ROLE_WEB).strip().lower()
    if service_role == SERVICE_ROLE_BULK_CREDENTIALS_WORKER:
        run_bulk_credentials_worker()
        return
    if service_role == SERVICE_ROLE_CIUDADANOS_IMPORT_WORKER:
        run_ciudadanos_import_worker()
        return
    run_django_commands()


def run_server():
    """
    Inicia el servidor de Django. Usa Gunicorn en produccion
    o el servidor de desarrollo si no.
    """
    environment = os.getenv("ENVIRONMENT", "dev").lower()
    deploy_gunicorn = environment in DEPLOY_GUNICORN_ENVIRONMENTS

    if deploy_gunicorn:
        cache_busting()
        logger.info("[server] Iniciando Django en modo produccion con Gunicorn...")
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
        logger.info("[server] Iniciando Django en modo desarrollo...")
        run_command(
            ["python", "manage.py", "runserver", "0.0.0.0:8000"],
            stage="runserver",
        )


def cache_busting():
    static_root = (
        Path(__file__).resolve().parent.parent / "static_root"
    )  # Raiz del proyecto
    if static_root.exists() and static_root.is_dir():
        logger.info("[clean] Eliminando carpeta de estaticos: %s", static_root)
        shutil.rmtree(static_root)
    logger.info("[static] Ejecutando collectstatic para cache busting...")
    run_command(
        ["python", "manage.py", "collectstatic", "--noinput"],
        stage="collectstatic",
        stdout=subprocess.DEVNULL,
    )


if __name__ == "__main__":
    main()
