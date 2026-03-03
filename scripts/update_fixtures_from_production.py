#!/usr/bin/env python3
"""Actualiza los fixtures con los datos que hay en producción."""

from __future__ import annotations

import argparse
import json
import logging
import os
import subprocess
import sys
from pathlib import Path

from dotenv import dotenv_values

REQUIRED_ENV_VARS = (
    "DATABASE_HOST",
    "DATABASE_NAME",
    "DATABASE_USER",
    "DATABASE_PASSWORD",
    "ENVIRONMENT",
    "DJANGO_SECRET_KEY",
)

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATTERN = "**/fixtures/*.json"


def configure_logging() -> None:
    logging.basicConfig(format="%(message)s", level=logging.INFO)


def load_env(env_file: Path) -> None:
    if not env_file.is_file():
        raise SystemExit(f"El archivo de entorno no existe: {env_file}")

    values = dotenv_values(env_file)
    if not values:
        raise SystemExit(f"No se pudo leer el archivo de entorno: {env_file}")

    for key, value in values.items():
        if value is None:
            continue
        stripped = value.strip()
        if not stripped:
            continue
        os.environ[key] = stripped


def verify_environment() -> None:
    missing = [var for var in REQUIRED_ENV_VARS if not os.environ.get(var)]
    if missing:
        raise SystemExit(
            "Faltan variables críticas en el entorno: " + ", ".join(missing)
        )

    if os.environ.get("ENVIRONMENT") != "prd":
        logging.warning(
            "ENVIRONMENT=%s (se recomienda usar prd para apuntar a producción)",
            os.environ.get("ENVIRONMENT"),
        )


def collect_fixture_paths() -> list[Path]:
    fixtures = sorted(REPO_ROOT.glob(FIXTURE_PATTERN))
    if not fixtures:
        raise SystemExit("No se encontraron fixtures bajo la ruta esperada.")
    return fixtures


def models_for_fixture(fixture_path: Path) -> list[str]:
    try:
        raw = fixture_path.read_text(encoding="utf-8")
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SystemExit(
            f"El fixture {fixture_path} no contiene JSON válido: {exc}"
        )

    if not isinstance(data, list):
        raise SystemExit(
            f"Se esperaba una lista en el fixture {fixture_path}, se encontró {type(data).__name__}."
        )

    models = {item.get("model") for item in data if isinstance(item, dict)}
    models = {model for model in models if isinstance(model, str)}
    return sorted(models)


def dump_models_to_fixture(models: list[str], fixture_path: Path) -> None:
    if not models:
        logging.info("Omite %s (no lista modelos).", fixture_path.relative_to(REPO_ROOT))
        return

    cmd = [sys.executable, "manage.py", "dumpdata", *models, "--indent", "4"]
    logging.info("Actualizando %s desde modelos %s", fixture_path.relative_to(REPO_ROOT), " ".join(models))
    with fixture_path.open("w", encoding="utf-8") as output:
        subprocess.run(cmd, cwd=REPO_ROOT, stdout=output, check=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Actualiza todos los fixtures desde la base de datos de producción."
    )
    parser.add_argument(
        "--env-file",
        dest="env_file",
        default=".env.prod",
        help="Ruta al archivo dotenv que apunta a la DB de producción (default: .env.prod)",
    )
    return parser.parse_args()


def main() -> None:
    configure_logging()
    args = parse_args()

    env_path = Path(args.env_file).expanduser().resolve()
    load_env(env_path)
    verify_environment()

    fixtures = collect_fixture_paths()
    for fixture_path in fixtures:
        models = models_for_fixture(fixture_path)
        dump_models_to_fixture(models, fixture_path)

    logging.info("Fixtures actualizados correctamente.")


if __name__ == "__main__":
    main()
