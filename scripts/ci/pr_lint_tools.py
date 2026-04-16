"""Utilidades compartidas para lint/autofix en GitHub Actions."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]

EXCLUDED_DIRS = {
    ".git",
    ".venv",
    "__pycache__",
    "node_modules",
    "staticfiles",
    "media",
}
EXCLUDED_SUFFIXES = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".svg",
    ".ico",
    ".webp",
    ".woff",
    ".woff2",
    ".ttf",
    ".eot",
    ".pdf",
    ".zip",
    ".sqlite3",
    ".pyc",
    ".pyo",
}
EXCLUDED_FILENAMES = {
    "package-lock.json",
    "poetry.lock",
}
TEMPLATE_SUFFIXES = {".html", ".htm", ".djhtml", ".jinja", ".j2"}
PYTHON_SUFFIXES = {".py"}
MOJIBAKE_REPLACEMENTS = {
    "\u00c3\u00a1": "\u00e1",
    "\u00c3\u00a9": "\u00e9",
    "\u00c3\u00ad": "\u00ed",
    "\u00c3\u00b3": "\u00f3",
    "\u00c3\u00ba": "\u00fa",
    "\u00c3\u00b1": "\u00f1",
    "\u00c3\u0081": "\u00c1",
    "\u00c3\u0089": "\u00c9",
    "\u00c3\u008d": "\u00cd",
    "\u00c3\u0093": "\u00d3",
    "\u00c3\u009a": "\u00da",
    "\u00c3\u0091": "\u00d1",
    "\u00c2\u00bf": "\u00bf",
    "\u00c2\u00a1": "\u00a1",
    "\u00c2\u00b0": "\u00b0",
    "\u00e2\u20ac\u2122": "\u2019",
    "\u00e2\u20ac\u0153": "\u201c",
    "\u00e2\u20ac\u009d": "\u201d",
    "\u00e2\u20ac\u201c": "\u2013",
    "\u00e2\u20ac\u201d": "\u2014",
    "\u00e2\u20ac\u00a6": "\u2026",
}


def read_event_payload() -> dict:
    """Carga el payload del evento actual de GitHub."""

    event_path = os.environ.get("GITHUB_EVENT_PATH")
    if not event_path:
        raise RuntimeError("GITHUB_EVENT_PATH no esta definido.")
    return json.loads(Path(event_path).read_text(encoding="utf-8"))


def get_diff_range() -> tuple[str, str]:
    """Devuelve el rango git relevante para el evento actual."""

    event_name = os.environ.get("GITHUB_EVENT_NAME")
    payload = read_event_payload()
    if event_name == "pull_request":
        return (
            payload["pull_request"]["base"]["sha"],
            payload["pull_request"]["head"]["sha"],
        )
    if event_name == "push":
        return payload["before"], payload["after"]
    raise RuntimeError(f"Evento no soportado: {event_name}")


def run_git_command(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    """Ejecuta un comando git dentro del repo compartiendo defaults de texto."""

    return subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=check,
    )


def parse_git_paths(output: str) -> list[Path]:
    """Normaliza una salida de git con rutas separadas por linea."""

    return [Path(item.strip()) for item in output.splitlines() if item.strip()]


def git_revision_exists(revision: str) -> bool:
    """Indica si una revision esta disponible en el checkout actual."""

    return (
        run_git_command(
            "rev-parse",
            "--verify",
            f"{revision}^{{commit}}",
            check=False,
        ).returncode
        == 0
    )


def get_fallback_changed_files() -> list[Path]:
    """Obtiene archivos relevantes aun cuando el rango base/head no esta disponible."""

    fallback_commands = (
        ("show", "--pretty=", "--name-only", "HEAD"),
        ("diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD"),
        ("ls-files",),
    )
    for command in fallback_commands:
        result = run_git_command(*command, check=False)
        files = parse_git_paths(result.stdout)
        if result.returncode == 0 and files:
            print(
                (
                    "Usando fallback para detectar archivos del PR "
                    f"con `git {' '.join(command)}`."
                ),
                file=sys.stderr,
            )
            return files
    return []


def get_changed_files() -> list[Path]:
    """Lista archivos cambiados dentro del rango del evento."""

    base_sha, head_sha = get_diff_range()
    if git_revision_exists(base_sha) and git_revision_exists(head_sha):
        result = run_git_command("diff", "--name-only", base_sha, head_sha)
        return parse_git_paths(result.stdout)

    print(
        (
            "No se encontro el rango git completo del evento "
            f"({base_sha}..{head_sha}); se usa una estrategia fallback."
        ),
        file=sys.stderr,
    )
    fallback_files = get_fallback_changed_files()
    if fallback_files:
        return fallback_files

    raise RuntimeError(
        "No fue posible detectar archivos modificados para el evento actual."
    )


def is_excluded(path: Path) -> bool:
    """Determina si un archivo debe quedar fuera de los chequeos de texto."""

    return (
        any(part in EXCLUDED_DIRS for part in path.parts)
        or path.name in EXCLUDED_FILENAMES
        or path.suffix.lower() in EXCLUDED_SUFFIXES
    )


def is_binary_content(data: bytes) -> bool:
    """Heuristica simple para ignorar blobs binarios."""

    return b"\x00" in data


def list_changed_files(kind: str) -> int:
    """Imprime como JSON los archivos cambiados relevantes para un tipo."""

    suffixes = TEMPLATE_SUFFIXES if kind == "templates" else PYTHON_SUFFIXES
    files = [
        str(path)
        for path in get_changed_files()
        if path.suffix.lower() in suffixes and (REPO_ROOT / path).is_file()
    ]
    print(json.dumps(files))
    return 0


def collect_text_files() -> tuple[list[tuple[Path, Path, bytes]], list[str]]:
    """Devuelve archivos de texto changed y archivos no UTF-8 que no se pueden tratar."""

    text_files: list[tuple[Path, Path, bytes]] = []
    undecodable: list[str] = []
    for relative_path in get_changed_files():
        absolute_path = REPO_ROOT / relative_path
        if not absolute_path.is_file() or is_excluded(relative_path):
            continue

        data = absolute_path.read_bytes()
        if is_binary_content(data):
            continue

        try:
            data.decode("utf-8")
        except UnicodeDecodeError as exc:
            undecodable.append(
                f"{relative_path}: archivo de texto no UTF-8, sin correccion segura ({exc})"
            )
            continue

        text_files.append((relative_path, absolute_path, data))

    return text_files, undecodable


def find_patterns(text: str) -> list[str]:
    """Busca secuencias de mojibake conocidas en un texto."""

    return [pattern for pattern in MOJIBAKE_REPLACEMENTS if pattern in text]


def format_findings(relative_path: Path, text: str) -> list[str]:
    """Construye findings por linea para la salida de CI."""

    findings: list[str] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        matches = [pattern for pattern in MOJIBAKE_REPLACEMENTS if pattern in line]
        if matches:
            findings.append(
                f"{relative_path}:{line_number}: patrones sospechosos {matches} -> {line.strip()}"
            )
    return findings


def normalize_text(text: str) -> tuple[str, int]:
    """Aplica reemplazos seguros de mojibake y devuelve la cantidad de cambios."""

    updated_text = text
    replacements = 0
    for source, target in MOJIBAKE_REPLACEMENTS.items():
        count = updated_text.count(source)
        if count:
            updated_text = updated_text.replace(source, target)
            replacements += count
    return updated_text, replacements


def check_encoding() -> int:
    """Falla si quedan patrones de mojibake o archivos no UTF-8 en el diff."""

    text_files, undecodable = collect_text_files()
    findings = list(undecodable)
    for relative_path, _, data in text_files:
        text = data.decode("utf-8")
        findings.extend(format_findings(relative_path, text))

    if findings:
        print("Problemas de encoding detectados:")
        for finding in findings:
            print(finding)
        return 1

    print(
        "No se detectaron problemas de encoding corregibles en los archivos cambiados."
    )
    return 0


def fix_encoding() -> int:
    """Normaliza mojibake segura en archivos changed y falla si queda algo sin resolver."""

    text_files, undecodable = collect_text_files()
    unresolved = list(undecodable)
    updated_files: list[str] = []

    for relative_path, absolute_path, data in text_files:
        original_text = data.decode("utf-8")
        normalized_text, replacements = normalize_text(original_text)
        if replacements:
            absolute_path.write_text(
                normalized_text,
                encoding="utf-8",
                newline="",
            )
            updated_files.append(f"{relative_path}: {replacements} reemplazo(s)")
        unresolved.extend(format_findings(relative_path, normalized_text))

    if updated_files:
        print("Archivos normalizados por encoding:")
        for updated_file in updated_files:
            print(updated_file)

    if unresolved:
        print("Persisten problemas de encoding que requieren correccion manual:")
        for finding in unresolved:
            print(finding)
        return 1

    print("Normalizacion de encoding completada sin problemas pendientes.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Construye el parser CLI del script."""

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    changed_files_parser = subparsers.add_parser("changed-files")
    changed_files_parser.add_argument(
        "--kind",
        choices=("python", "templates"),
        required=True,
    )

    subparsers.add_parser("check-encoding")
    subparsers.add_parser("fix-encoding")
    return parser


def main() -> int:
    """Punto de entrada CLI."""

    parser = build_parser()
    args = parser.parse_args()

    if args.command == "changed-files":
        return list_changed_files(args.kind)
    if args.command == "check-encoding":
        return check_encoding()
    if args.command == "fix-encoding":
        return fix_encoding()
    parser.error(f"Comando no soportado: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
