import os
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor
import pymysql


def wait_for_mysql():
    host = os.getenv("DATABASE_HOST", "mysql")
    port = int(os.getenv("DATABASE_PORT", "3307"))
    user = os.getenv("DATABASE_USER", "root")
    password = os.getenv("DATABASE_PASSWORD", "root1-password2")

    wait_for_db = os.getenv("WAIT_FOR_DB", "true").lower() == "true"

    if not wait_for_db:
        print("Skipping waiting for MySQL as WAIT_FOR_DB is set to false.")
        return

    print("Waiting for MySQL to be ready...")
    while True:
        try:
            conn = pymysql.connect(host=host, port=port, user=user, password=password)
            conn.close()
            break
        except pymysql.MySQLError:
            time.sleep(5)
    time.sleep(10)
    print("MySQL is up and ready")


def run_django_commands():
    subprocess.run(["python", "manage.py", "makemigrations"])
    subprocess.run(["python", "manage.py", "migrate", "--noinput"])
    load_fixtures()
    subprocess.run(["python", "manage.py", "create_local_superuser"])
    subprocess.run(["python", "manage.py", "create_groups"])
    run_server()


def run_server():
    environment = os.getenv("ENVIRONMENT", "dev").lower()

    if environment == "prd":
        print("Running Django in production mode with Gunicorn...")
        subprocess.run(["gunicorn", "config.asgi:application", "-k", "uvicorn.workers.UvicornWorker",
                        "-b", "0.0.0.0:8000", "--workers", "4", "--threads", "2", "--log-level", "info"])
    else:
        print("Running Django in development mode...")
        subprocess.run(["python", "manage.py", "runserver", "0.0.0.0:8000"])


def load_fixture(file):
    subprocess.run(["python", "manage.py", "loaddata", file])


def load_fixtures():
    fixtures = []
    for root, dirs, _ in os.walk("."):
        if "fixtures" in dirs:
            fixtures_dir = os.path.join(root, "fixtures")
            fixtures.extend(
                [
                    os.path.join(fixtures_dir, file)
                    for file in os.listdir(fixtures_dir)
                    if file.endswith(".json")
                ]
            )

    with ThreadPoolExecutor() as executor:
        executor.map(load_fixture, fixtures)


if __name__ == "__main__":
    wait_for_mysql()
    run_django_commands()
