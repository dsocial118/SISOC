import os
import time
import subprocess
import pymysql


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
    subprocess.run(["python", "manage.py", "runserver", "0.0.0.0:8000"])


if __name__ == "__main__":
    wait_for_mysql()
    run_django_commands()
