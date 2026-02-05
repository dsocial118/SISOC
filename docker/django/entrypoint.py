import logging
import os
import subprocess
import time
import pymysql
import shutil
from pathlib import Path


if not logging.getLogger().handlers:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("django")


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

    def flag(name: str, default: bool) -> bool:
        return os.getenv(name, str(default)).lower() == "true"

    run_makemigrations = flag("RUN_MAKEMIGRATIONS", environment == "dev")
    run_migrations = flag("RUN_MIGRATIONS", True)
    load_fixtures = flag("LOAD_FIXTURES", environment == "dev")
    create_test_users = flag("CREATE_TEST_USERS", environment == "dev")
    create_groups = flag("CREATE_GROUPS", True)

    if run_makemigrations:
        subprocess.run(["python", "manage.py", "makemigrations"], check=True)
    if run_migrations:
        subprocess.run(["python", "manage.py", "migrate", "auth"], check=True)
        subprocess.run(["python", "manage.py", "migrate", "--noinput"], check=True)
    if load_fixtures:
        subprocess.run(["python", "manage.py", "load_fixtures"], check=True)
    if create_test_users:
        subprocess.run(["python", "manage.py", "create_test_users"], check=True)
    if create_groups:
        subprocess.run(["python", "manage.py", "create_groups"], check=True)
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
        subprocess.run(cmd)
    else:
        logger.info("🧪 Iniciando Django en modo desarrollo...")
        subprocess.run(["python", "manage.py", "runserver", "0.0.0.0:8000"])


def cache_busting():
    static_root = (
        Path(__file__).resolve().parent.parent / "static_root"
    )  # Raíz del proyecto
    if static_root.exists() and static_root.is_dir():
        logger.info("🧹 Eliminando carpeta de estáticos: %s", static_root)
        shutil.rmtree(static_root)
    logger.info("📦 Ejecutando collectstatic para cache busting...")
    subprocess.run(
        ["python", "manage.py", "collectstatic", "--noinput"],
        stdout=subprocess.DEVNULL,
    )


if __name__ == "__main__":
    wait_for_mysql()
    run_django_commands()
