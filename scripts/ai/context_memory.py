"""Herramientas para memoria operativa de contexto IA."""

from __future__ import annotations

import argparse
import ast
import json
import subprocess
import sys
from dataclasses import dataclass
from datetime import date
from fnmatch import fnmatch
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
VERSIONED_MEMORY_DIR = REPO_ROOT / "docs" / "contexto" / "memoria"
LOCAL_MEMORY_DIR = REPO_ROOT / ".codex" / "cache" / "context-memory"
FRONTMATTER_DELIMITER = "+++"


class MemoryDocumentError(ValueError):
    """Error de formato en un documento de memoria."""


@dataclass(frozen=True)
class MemoryStatus:
    """Estado de frescura de una memoria."""

    state: str
    changed_files: tuple[str, ...]
    reason: str


@dataclass(frozen=True)
class MemoryDocument:
    """Documento de memoria operativa cargado desde Markdown."""

    path: Path
    key: str
    title: str
    summary: str
    tracked_paths: tuple[str, ...]
    validated_commit: str
    validated_at: str
    confidence: str
    is_default: bool
    body: str
    source: str

    @property
    def relative_path(self) -> str:
        """Devuelve el path relativo al repo."""

        return normalize_repo_path(self.path.relative_to(REPO_ROOT).as_posix())

    def matches_target(self, target_path: str) -> bool:
        """Indica si la memoria aplica al path pedido."""

        normalized_target = normalize_repo_path(target_path)
        return any(
            path_pattern_matches(pattern, normalized_target)
            for pattern in self.tracked_paths
        )


def normalize_repo_path(value: str) -> str:
    """Normaliza un path relativo al repo a formato posix."""

    normalized = value.replace("\\", "/").strip()
    while normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized.strip("/")


def path_pattern_matches(pattern: str, relative_path: str) -> bool:
    """Evalua si un path relativo matchea un patron simple."""

    normalized_pattern = normalize_repo_path(pattern)
    normalized_target = normalize_repo_path(relative_path)
    if not normalized_pattern:
        return False
    if any(char in normalized_pattern for char in "*?["):
        return fnmatch(normalized_target, normalized_pattern)
    if pattern.endswith("/"):
        return normalized_target.startswith(f"{normalized_pattern}/")
    return normalized_target == normalized_pattern or normalized_target.startswith(
        f"{normalized_pattern}/"
    )


def split_frontmatter(text: str) -> tuple[str, str]:
    """Separa frontmatter TOML y cuerpo Markdown."""

    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != FRONTMATTER_DELIMITER:
        raise MemoryDocumentError(
            "El documento no tiene frontmatter TOML delimitado con +++."
        )
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == FRONTMATTER_DELIMITER:
            frontmatter = "".join(lines[1:index])
            body = "".join(lines[index + 1 :])
            return frontmatter, body
    raise MemoryDocumentError("No se encontro el cierre del frontmatter TOML.")


def parse_frontmatter_value(raw_value: str) -> Any:
    """Parsea un valor simple del frontmatter generado por esta herramienta."""

    value = raw_value.strip()
    if value in {"true", "false"}:
        return value == "true"
    if value.startswith("[") or value.startswith('"'):
        try:
            return ast.literal_eval(value)
        except (SyntaxError, ValueError) as error:
            raise MemoryDocumentError("Valor invalido en frontmatter.") from error
    return value


def parse_frontmatter(frontmatter: str) -> dict[str, Any]:
    """Parsea el subset de TOML/JSON usado por las memorias del repo."""

    metadata: dict[str, Any] = {}
    lines = frontmatter.splitlines()
    index = 0
    while index < len(lines):
        raw_line = lines[index]
        index += 1
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise MemoryDocumentError("Linea invalida en frontmatter.")
        key, raw_value = line.split("=", 1)
        serialized_value = raw_value.strip()
        if serialized_value.startswith("[") and not serialized_value.endswith("]"):
            while index < len(lines):
                serialized_value = f"{serialized_value} {lines[index].strip()}"
                index += 1
                if serialized_value.endswith("]"):
                    break
        metadata[key.strip()] = parse_frontmatter_value(serialized_value)
    return metadata


def load_memory_document(path: Path, source: str) -> MemoryDocument:
    """Carga un documento de memoria desde disco."""

    frontmatter, body = split_frontmatter(path.read_text(encoding="utf-8"))
    metadata = parse_frontmatter(frontmatter)
    tracked_paths = tuple(
        normalize_repo_path(item) for item in metadata.get("paths", [])
    )
    if not tracked_paths:
        raise MemoryDocumentError(f"{path} no define 'paths'.")
    return MemoryDocument(
        path=path,
        key=str(metadata["key"]),
        title=str(metadata["title"]),
        summary=str(metadata["summary"]),
        tracked_paths=tracked_paths,
        validated_commit=str(metadata.get("validated_commit", "")).strip(),
        validated_at=str(metadata.get("validated_at", "")).strip(),
        confidence=str(metadata.get("confidence", "media")).strip() or "media",
        is_default=bool(metadata.get("default", False)),
        body=body.lstrip("\n"),
        source=source,
    )


def iter_memory_files(directory: Path) -> list[Path]:
    """Lista archivos Markdown candidatos dentro de un directorio."""

    if not directory.exists():
        return []
    return sorted(
        path
        for path in directory.glob("*.md")
        if path.name not in {"README.md", "TEMPLATE.md"}
    )


def load_all_memory_documents() -> list[MemoryDocument]:
    """Carga memorias versionadas y locales, priorizando las locales por key."""

    documents_by_key: dict[str, MemoryDocument] = {}
    for source, directory in (
        ("versioned", VERSIONED_MEMORY_DIR),
        ("local", LOCAL_MEMORY_DIR),
    ):
        for path in iter_memory_files(directory):
            try:
                document = load_memory_document(path, source)
            except (OSError, KeyError, MemoryDocumentError):
                continue
            documents_by_key[document.key] = document
    return sorted(
        documents_by_key.values(), key=lambda item: (not item.is_default, item.key)
    )


def run_git_command(args: list[str]) -> subprocess.CompletedProcess[str]:
    """Ejecuta un comando git relativo al repo."""

    return subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def git_command_output(args: list[str]) -> list[str]:
    """Devuelve la salida de git como lineas limpias."""

    result = run_git_command(args)
    if result.returncode != 0:
        return []
    return [
        normalize_repo_path(line) for line in result.stdout.splitlines() if line.strip()
    ]


def validated_commit_exists(commit: str) -> bool:
    """Valida si un commit existe en el repo."""

    if not commit:
        return False
    result = run_git_command(["rev-parse", "--verify", "--quiet", commit])
    return result.returncode == 0


def tracked_path_matches(document: MemoryDocument, relative_path: str) -> bool:
    """Indica si un archivo cambiado afecta la memoria."""

    return any(
        path_pattern_matches(pattern, relative_path)
        for pattern in document.tracked_paths
    )


def collect_relevant_changes(document: MemoryDocument) -> tuple[str, ...]:
    """Devuelve archivos relevantes cambiados desde la validacion de la memoria."""

    if not document.validated_commit or not validated_commit_exists(
        document.validated_commit
    ):
        return ()

    changed_files: set[str] = set()
    for git_args in (
        ["diff", "--name-only", f"{document.validated_commit}..HEAD"],
        ["diff", "--cached", "--name-only"],
        ["diff", "--name-only"],
    ):
        changed_files.update(git_command_output(git_args))
    return tuple(
        sorted(path for path in changed_files if tracked_path_matches(document, path))
    )


def evaluate_memory_status(document: MemoryDocument) -> MemoryStatus:
    """Determina si la memoria sigue fresca respecto del repo actual."""

    if not document.validated_commit:
        return MemoryStatus(
            state="unknown",
            changed_files=(),
            reason="sin validated_commit",
        )
    if not validated_commit_exists(document.validated_commit):
        return MemoryStatus(
            state="unknown",
            changed_files=(),
            reason="validated_commit inexistente",
        )
    changed_files = collect_relevant_changes(document)
    if changed_files:
        return MemoryStatus(
            state="stale",
            changed_files=changed_files,
            reason="hay cambios en paths seguidos desde la ultima validacion",
        )
    return MemoryStatus(
        state="fresh", changed_files=(), reason="sin cambios relevantes"
    )


def resolve_documents(target_path: str | None) -> list[MemoryDocument]:
    """Resuelve las memorias relevantes para un path objetivo."""

    documents = load_all_memory_documents()
    default_documents = [document for document in documents if document.is_default]
    if not target_path:
        return default_documents or documents

    matched_documents = [
        document for document in documents if document.matches_target(target_path)
    ]
    resolved: list[MemoryDocument] = []
    seen_keys: set[str] = set()
    for document in [*matched_documents, *default_documents]:
        if document.key in seen_keys:
            continue
        resolved.append(document)
        seen_keys.add(document.key)
    return resolved


def relative_target_path(target_path: str) -> str:
    """Resuelve el path relativo al repo para un target cualquiera."""

    candidate = Path(target_path)
    if candidate.is_absolute():
        try:
            return normalize_repo_path(candidate.relative_to(REPO_ROOT).as_posix())
        except ValueError:
            return normalize_repo_path(candidate.as_posix())
    return normalize_repo_path(target_path)


def metadata_from_document(document: MemoryDocument) -> dict[str, Any]:
    """Serializa metadata canonica para escritura."""

    return {
        "key": document.key,
        "title": document.title,
        "summary": document.summary,
        "paths": list(document.tracked_paths),
        "default": document.is_default,
        "confidence": document.confidence,
        "validated_commit": document.validated_commit,
        "validated_at": document.validated_at,
    }


def render_frontmatter(metadata: dict[str, Any]) -> str:
    """Renderiza frontmatter TOML en un orden estable."""

    ordered_keys = (
        "key",
        "title",
        "summary",
        "paths",
        "default",
        "confidence",
        "validated_commit",
        "validated_at",
    )
    lines = [FRONTMATTER_DELIMITER]
    for key in ordered_keys:
        if key not in metadata:
            continue
        lines.append(f"{key} = {json.dumps(metadata[key], ensure_ascii=True)}")
    lines.append(FRONTMATTER_DELIMITER)
    return "\n".join(lines)


def current_head_short() -> str:
    """Obtiene el short SHA de HEAD."""

    output = git_command_output(["rev-parse", "--short", "HEAD"])
    return output[0] if output else ""


def scaffold_body(title: str) -> str:
    """Genera el cuerpo inicial para una memoria nueva."""

    return f"""# {title}

## Estado
- Ultima validacion manual: completar o ajustar si hace falta.
- Fuentes revisadas: listar codigo, tests o docs inspeccionados.

## Propósito
- Describir en 2-3 bullets que resuelve este modulo o flujo.

## Entry points y archivos clave
- Enumerar views, services, serializers, comandos o templates relevantes.

## Patrones y contratos utiles
- Anotar limites de capas, side effects, permisos o invariantes.

## Como validar rapido
- Dejar comandos o tests minimos para reconstruir confianza.

## Cuando invalidar esta memoria
- Listar cambios que obligan a releer codigo antes de reutilizarla.
"""


def write_memory_file(path: Path, metadata: dict[str, Any], body: str) -> None:
    """Escribe un documento de memoria en disco."""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"{render_frontmatter(metadata)}\n\n{body.rstrip()}\n",
        encoding="utf-8",
    )


def command_preflight(target: str | None) -> int:
    """Renderiza memoria util para el preflight."""

    target_path = relative_target_path(target) if target else None
    documents = resolve_documents(target_path)
    print("== Memoria de contexto reutilizable ==")
    if target_path:
        print(f"Target normalizado: {target_path}")
    if not documents:
        print("- No hay memorias registradas para este target.")
        print(
            "- Crear una con: "
            "python scripts/ai/context_memory.py scaffold --slug <slug> "
            "--title <titulo> --summary <resumen> --path <path>"
        )
        return 0

    for document in documents:
        status = evaluate_memory_status(document)
        print(
            f"- {document.relative_path} "
            f"[{status.state} | fuente={document.source} | confianza={document.confidence}]"
        )
        print(f"  resumen: {document.summary}")
        print(
            "  validada: "
            f"{document.validated_commit or 'sin commit'} / "
            f"{document.validated_at or 'sin fecha'}"
        )
        if status.changed_files:
            print(f"  cambios relevantes: {', '.join(status.changed_files[:5])}")
        else:
            print(f"  estado: {status.reason}")
    print(
        "- Cache local opcional: "
        ".codex/cache/context-memory/ (gitignored, util para analisis efimeros)."
    )
    return 0


def command_resolve(target: str, output_format: str) -> int:
    """Resuelve documentos para un target y los imprime."""

    target_path = relative_target_path(target)
    documents = resolve_documents(target_path)
    if output_format == "json":
        payload = []
        for document in documents:
            status = evaluate_memory_status(document)
            payload.append(
                {
                    "key": document.key,
                    "title": document.title,
                    "summary": document.summary,
                    "path": document.relative_path,
                    "source": document.source,
                    "status": status.state,
                    "changed_files": list(status.changed_files),
                    "validated_commit": document.validated_commit,
                    "validated_at": document.validated_at,
                    "confidence": document.confidence,
                }
            )
        print(json.dumps(payload, ensure_ascii=True, indent=2))
        return 0

    if not documents:
        print(f"No hay memorias registradas para {target_path}.")
        return 1

    for document in documents:
        status = evaluate_memory_status(document)
        print(
            f"{document.relative_path}\t{document.source}\t{status.state}\t{document.summary}"
        )
    return 0


def command_scaffold(args: argparse.Namespace) -> int:
    """Crea una memoria nueva con plantilla."""

    destination_dir = LOCAL_MEMORY_DIR if args.local else VERSIONED_MEMORY_DIR
    destination = destination_dir / f"{args.slug}.md"
    metadata = {
        "key": args.slug,
        "title": args.title,
        "summary": args.summary,
        "paths": [normalize_repo_path(path) for path in args.paths],
        "default": args.default,
        "confidence": args.confidence,
        "validated_commit": args.validated_commit or current_head_short(),
        "validated_at": args.validated_at or date.today().isoformat(),
    }
    if destination.exists() and not args.force:
        raise SystemExit(f"El archivo ya existe: {destination}")
    write_memory_file(destination, metadata, scaffold_body(args.title))
    print(normalize_repo_path(destination.relative_to(REPO_ROOT).as_posix()))
    return 0


def command_refresh(args: argparse.Namespace) -> int:
    """Actualiza metadata de validacion en una memoria existente."""

    memory_path = Path(args.file)
    if not memory_path.is_absolute():
        memory_path = REPO_ROOT / memory_path
    document = load_memory_document(
        memory_path, "local" if LOCAL_MEMORY_DIR in memory_path.parents else "versioned"
    )
    metadata = metadata_from_document(document)
    metadata["validated_commit"] = args.validated_commit or current_head_short()
    metadata["validated_at"] = args.validated_at or date.today().isoformat()
    if args.summary:
        metadata["summary"] = args.summary
    if args.confidence:
        metadata["confidence"] = args.confidence
    write_memory_file(memory_path, metadata, document.body)
    print(normalize_repo_path(memory_path.relative_to(REPO_ROOT).as_posix()))
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Construye el parser principal."""

    parser = argparse.ArgumentParser(
        description="Gestiona memoria operativa reutilizable para asistentes sobre SISOC."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    preflight_parser = subparsers.add_parser(
        "preflight",
        help="Imprime la memoria util para el arranque de una tarea.",
    )
    preflight_parser.add_argument("--target", help="Path objetivo relativo o absoluto.")

    resolve_parser = subparsers.add_parser(
        "resolve",
        help="Resuelve memorias aplicables a un path.",
    )
    resolve_parser.add_argument("--target", required=True, help="Path objetivo.")
    resolve_parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Formato de salida.",
    )

    scaffold_parser = subparsers.add_parser(
        "scaffold",
        help="Crea una memoria nueva desde plantilla.",
    )
    scaffold_parser.add_argument(
        "--slug", required=True, help="Slug y key de la memoria."
    )
    scaffold_parser.add_argument("--title", required=True, help="Titulo del documento.")
    scaffold_parser.add_argument(
        "--summary", required=True, help="Resumen corto reutilizable."
    )
    scaffold_parser.add_argument(
        "--path",
        dest="paths",
        action="append",
        required=True,
        help="Path o patron seguido por la memoria. Repetible.",
    )
    scaffold_parser.add_argument(
        "--confidence",
        default="media",
        help="Nivel de confianza inicial (alta/media/baja).",
    )
    scaffold_parser.add_argument(
        "--validated-commit",
        help="Commit base para invalidacion. Default: HEAD actual.",
    )
    scaffold_parser.add_argument(
        "--validated-at",
        help="Fecha ISO de validacion. Default: hoy.",
    )
    scaffold_parser.add_argument(
        "--default",
        action="store_true",
        help="Hace que la memoria aparezca tambien sin target.",
    )
    scaffold_parser.add_argument(
        "--local",
        action="store_true",
        help="Guarda la memoria en .codex/cache/context-memory/.",
    )
    scaffold_parser.add_argument(
        "--force",
        action="store_true",
        help="Sobrescribe si ya existe.",
    )

    refresh_parser = subparsers.add_parser(
        "refresh",
        help="Actualiza metadata de validacion en una memoria existente.",
    )
    refresh_parser.add_argument(
        "--file", required=True, help="Ruta del archivo de memoria."
    )
    refresh_parser.add_argument("--validated-commit", help="Nuevo commit validado.")
    refresh_parser.add_argument("--validated-at", help="Nueva fecha ISO.")
    refresh_parser.add_argument("--summary", help="Resumen actualizado opcional.")
    refresh_parser.add_argument("--confidence", help="Confianza actualizada opcional.")

    return parser


def main(argv: list[str] | None = None) -> int:
    """Punto de entrada CLI."""

    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "preflight":
        return command_preflight(args.target)
    if args.command == "resolve":
        return command_resolve(args.target, args.format)
    if args.command == "scaffold":
        return command_scaffold(args)
    if args.command == "refresh":
        return command_refresh(args)
    parser.error(f"Comando no soportado: {args.command}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
