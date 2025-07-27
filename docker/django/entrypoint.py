import os
import sys
import time
import shutil
import pymysql
from pathlib import Path
from typing import Optional
from subprocess import run, CalledProcessError
from contextlib import closing

# ---------- Utils ----------


def env_bool(name: str, default: str = "false") -> bool:
    return os.getenv(name, default).strip().lower() in {"1", "true", "yes", "y"}


def env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        return default


def sh(cmd: list[str], check: bool = True) -> None:
    print(f"▶️  {' '.join(cmd)}")
    try:
        run(cmd, check=check)
    except CalledProcessError as e:
        print(f"❌ Comando falló ({e.returncode}): {' '.join(cmd)}")
        sys.exit(e.returncode)


# ---------- DB helpers ----------


def mysql_connect():
    host = os.getenv("DATABASE_HOST")
    port = int(os.getenv("DATABASE_PORT", 3306))
    user = os.getenv("DATABASE_USER")
    pwd = os.getenv("DATABASE_PASSWORD")
    return pymysql.connect(host=host, port=port, user=user, password=pwd)


def get_mysql_variable(var: str, default: Optional[int] = None) -> Optional[int]:
    try:
        with closing(mysql_connect()) as conn, closing(conn.cursor()) as cur:
            cur.execute("SHOW VARIABLES LIKE %s;", (var,))
            row = cur.fetchone()
            if row:
                return int(row[1])
    except Exception as e:
        print(f"⚠️  No pude leer {var} de MySQL: {e}")
    return default


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
            delay = min(delay * 2, 10)


# ---------- Django prep ----------


def django_prepare(env: str):
    """
    - makemigrations solo fuera de PRD/QA (punto 1/A)
    - subprocess con check (2/B)
    - create_test_users & create_groups en todo menos PRD (6)
    - check --deploy en PRD (F)
    """
    is_prd = env == "prd"

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


# ---------- Gunicorn tuning (Punto 2) ----------


def calc_gunicorn_params():
    """
    Calcula workers y threads coherentes con:
      - CPUs disponibles
      - max_connections de MySQL
    Reglas:
      - threads = 1 con UvicornWorker
      - workers = min( (2*cpus)+1 , max((max_connections - margen)/2, 1) )
        donde '2' es factor de seguridad por conexiones por worker
    Permite overrides por env vars.
    """
    # Overrides explícitos
    forced_workers = os.getenv("GUNICORN_WORKERS")
    forced_threads = os.getenv("GUNICORN_THREADS")

    if forced_workers and forced_threads:
        return forced_workers, forced_threads

    cpus = os.cpu_count() or 2
    default_workers = (2 * cpus) + 1

    # margen para admin/replicas/otros servicios
    margin = env_int("DB_CONN_MARGIN", 20)
    factor = env_int("DB_CONN_PER_WORKER_FACTOR", 2)

    max_conns = get_mysql_variable("max_connections", default=151)
    if max_conns and max_conns > margin:
        max_by_db = max((max_conns - margin) // factor, 1)
    else:
        max_by_db = default_workers  # fallback si no pudimos leer

    workers = min(default_workers, max_by_db)
    workers = env_int("GUNICORN_WORKERS", workers)  # si solo seteás uno

    threads = env_int("GUNICORN_THREADS", 1)  # fuerza 1 por defecto

    return str(workers), str(threads)


# ---------- Run server ----------


def run_server(env: str):
    if env == "prd":
        workers, threads = calc_gunicorn_params()

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
            threads,  # debería ser 1 por diseño
            "--timeout",
            os.getenv("GUNICORN_TIMEOUT", "30"),
            "--max-requests",
            os.getenv("GUNICORN_MAX_REQUESTS", "800"),
            "--max-requests-jitter",
            os.getenv("GUNICORN_MAX_REQUESTS_JITTER", "80"),
            "--log-level",
            os.getenv("GUNICORN_LOG_LEVEL", "info"),
            "--access-logfile",
            "-",
        ]
        print(f"🚀 Lanzando Gunicorn con workers={workers}, threads={threads}")
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
