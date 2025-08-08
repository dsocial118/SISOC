import os
import subprocess
import time
import pymysql
import shutil
from pathlib import Path


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
        print("⏭️  Se omite la espera por MySQL (WAIT_FOR_DB=false)")
        return

    if not all([host, user, password]):
        print(
            "❌ Error: Faltan variables de entorno para la conexión a la base de datos"
        )
        print(
            "   Asegúrese de definir DATABASE_HOST, DATABASE_USER y DATABASE_PASSWORD"
        )
        return

    print("⏳ Esperando que MySQL esté disponible...")
    while True:
        try:
            conn = pymysql.connect(host=host, port=port, user=user, password=password)
            conn.close()
            break
        except pymysql.MySQLError:
            time.sleep(5)
    time.sleep(10)
    print("✅ MySQL está listo.")


def run_django_commands():
    """
    Ejecuta los comandos de Django necesarios para la preparación y el funcionamiento de la aplicación.
    """
    subprocess.run(["python", "manage.py", "makemigrations"])
    subprocess.run(["python", "manage.py", "migrate", "auth"])
    subprocess.run(["python", "manage.py", "migrate", "--noinput"])

    # Cargar los fixtures condicionalmente, si se quiere forzar añadir `--force`
    subprocess.run(["python", "manage.py", "load_fixtures"])

    subprocess.run(["python", "manage.py", "create_test_users"])
    subprocess.run(["python", "manage.py", "create_groups"])
    run_server()


def run_server():
    """
    Inicia el servidor de Django. Usa Gunicorn en producción o el servidor de desarrollo si no.
    """
    environment = os.getenv("ENVIRONMENT", "dev").lower()
    deploy_gunicorn = environment in ("prd", "qa")

    if deploy_gunicorn:
        cache_busting()
        print("🚀 Iniciando Django en modo producción con Gunicorn...")
        subprocess.run(
            [
                "gunicorn",
                "config.asgi:application",
                "-k",
                "uvicorn.workers.UvicornWorker",
                "-b",
                "0.0.0.0:8000",
                "--workers",
                "4",
                "--threads",
                "2",
                "--log-level",
                "info",
            ]
        )
    else:
        print("🧪 Iniciando Django en modo desarrollo...")
        subprocess.run(["python", "manage.py", "runserver", "0.0.0.0:8000"])


def cache_busting():
    static_root = (
        Path(__file__).resolve().parent.parent / "static_root"
    )  # Raíz del proyecto
    if static_root.exists() and static_root.is_dir():
        print(f"🧹 Eliminando carpeta de estáticos: {static_root}")
        shutil.rmtree(static_root)
    print("📦 Ejecutando collectstatic para cache busting...")
    subprocess.run(["python", "manage.py", "collectstatic", "--noinput"])


if __name__ == "__main__":
    wait_for_mysql()
    run_django_commands()
