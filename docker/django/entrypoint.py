import os
import sys
import time
import shutil
from pathlib import Path
from subprocess import run, CalledProcessError
import pymysql


# ---------- Utils ----------


def env_bool(name: str, default: str = "false") -> bool:
    return os.getenv(name, default).strip().lower() in {"1", "true", "yes", "y"}


def sh(cmd: list[str], check: bool = True) -> None:
    """Run shell cmd, fail fast with clear error."""
    print(f"▶️  {' '.join(cmd)}")
    try:
        run(cmd, check=check)
    except CalledProcessError as e:
        print(f"❌ Comando falló ({e.returncode}): {' '.join(cmd)}")
        sys.exit(e.returncode)


# ---------- DB wait ----------

def wait_for_mysql():
    if not env_bool("WAIT_FOR_DB", "true"):
        print("⏭️  Skip wait for DB")
        return

    host = os.getenv("DATABASE_HOST")
    port = int(os.getenv("DATABASE_PORT", 3306))
    user = os.getenv("DATABASE_USER")
    pwd = os.getenv("DATABASE_PASSWORD")

    if not all([host, user, pwd]):
        print("❌ Faltan vars de DB (DATABASE_HOST/USER/PASSWORD).")
        sys.exit(1)

    max_wait = int(os.getenv("MAX_DB_WAIT_SECONDS", "120"))
    delay = 1
    start = time.time()

    print("⏳ Esperando MySQL...")
    while True:
        try:
            pymysql.connect(host=host, port=port, user=user, password=pwd).close()
            print("✅ MySQL listo.")
            return
        except pymysql.MySQLError as e:
            if time.time() - start > max_wait:
                print(f"❌ MySQL no respondió en {max_wait}s: {e}")
                sys.exit(1)
            time.sleep(delay)
            delay = min(delay * 2, 10)  # backoff exponencial, máx 10s


# ---------- Django prep ----------


def django_prepare(env: str):
    """
    - makemigrations solo fuera de PRD/QA (punto 1/A)
    - subprocess con check (2/B)
    - create_test_users & create_groups en todo menos PRD (6)
    - check --deploy en PRD (F)
    """
    is_prd = env == "prd"

    # Makemigrations solo si no es PRD ni QA (asumo QA == 'qa')
    if env not in {"prd", "qa"} and env_bool("RUN_MAKEMIGRATIONS", "true"):
        sh(["python", "manage.py", "makemigrations"])

    if env_bool("RUN_MIGRATIONS", "true"):
        sh(["python", "manage.py", "migrate", "--noinput"])

    if env_bool("RUN_FIXTURES", "false"):
        sh(["python", "manage.py", "load_fixtures"])

    if not is_prd and env_bool("RUN_SETUP_TASKS", "true"):
        sh(["python", "manage.py", "create_test_users"])
        sh(["python", "manage.py", "create_groups"])

    if is_prd and env_bool("RUN_CHECKS", "true"):
        sh(["python", "manage.py", "check", "--deploy"])


def maybe_collectstatic():
    if not env_bool("RUN_COLLECTSTATIC", "false"):
        return
    static_root = Path(os.getenv("STATIC_ROOT", "static_root"))
    if static_root.exists():
        print(f"🧹 Borrando STATIC_ROOT: {static_root}")
        shutil.rmtree(static_root)
    sh(["python", "manage.py", "collectstatic", "--noinput"])


# ---------- Run server ----------


def run_server(env: str):
    if env == "prd":
        # Gunicorn configurable (8)
        workers = os.getenv("GUNICORN_WORKERS") or str(max(2, os.cpu_count() * 2 + 1))
        args = [
            "gunicorn",
            "config.asgi:application",
            "-k",
            "uvicorn.workers.UvicornWorker",
            "-b",
            os.getenv("BIND", "0.0.0.0:8000"),
            "--workers",
            workers,
            "--threads",
            os.getenv("GUNICORN_THREADS", "2"),
            "--timeout",
            os.getenv("GUNICORN_TIMEOUT", "30"),
            "--max-requests",
            os.getenv("GUNICORN_MAX_REQUESTS", "1000"),
            "--log-level",
            os.getenv("GUNICORN_LOG_LEVEL", "info"),
            "--access-logfile",
            "-",
        ]
        # Reemplaza el proceso actual (D)
        os.execvp(args[0], args)
    else:
        os.execvp("python", ["python", "manage.py", "runserver", "0.0.0.0:8000"])


# ---------- Main ----------

if __name__ == "__main__":
    ENV = os.getenv("ENVIRONMENT", "dev").strip().lower()

    wait_for_mysql()
    django_prepare(ENV)
    maybe_collectstatic()
    run_server(ENV)
