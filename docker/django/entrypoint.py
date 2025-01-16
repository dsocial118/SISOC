import os
import subprocess
import time

import pymysql

from concurrent.futures import ThreadPoolExecutor

def wait_for_mysql():
    host = os.getenv("DATABASE_HOST", "mysql")
    port = int(os.getenv("DATABASE_PORT", 3307))

    print("Waiting for MySQL to be ready...")
    while True:
        try:
            conn = pymysql.connect(
                host=host, port=port, user="root", password="root1-password2"
            )
            conn.close()
            break
        except pymysql.MySQLError:
            time.sleep(5)

    # Añade un delay para asegurar que el dump de MySQL se procese completamente
    time.sleep(10)
    print("MySQL is up and ready")


def run_django_commands():
    subprocess.run(["python", "manage.py", "makemigrations"])
    subprocess.run(["python", "manage.py", "migrate", "--noinput"])
    load_fixtures()
    subprocess.run(["python", "manage.py", "create_local_superuser"])
    subprocess.run(["python", "manage.py", "runserver", "0.0.0.0:8000"])


def load_fixture(file):
    subprocess.run(["python", "manage.py", "loaddata", file])


def load_fixtures():
    fixtures = []
    for root, dirs, files in os.walk("."):
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
