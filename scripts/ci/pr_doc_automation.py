"""Genera artefactos spec-as-source y changelog a partir de un pull request."""

from __future__ import annotations

import json
import os
import re
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
DOCS_PR_DIR = REPO_ROOT / "docs/registro/prs"
DOCS_FEATURE_DIR = REPO_ROOT / "docs/contexto/features"
DOCS_RELEASE_PENDING_DIR = REPO_ROOT / "docs/registro/releases/pending"
CHANGELOG_PATH = REPO_ROOT / "CHANGELOG.md"

AUTO_RELEASE_START = "<!-- AUTO-GENERATED RELEASE START: {release_date} -->"
AUTO_RELEASE_END = "<!-- AUTO-GENERATED RELEASE END: {release_date} -->"

GENERIC_TOP_LEVEL = {
    ".github",
    "docs",
    "tests",
    "scripts",
    "docker",
    "static",
    "static_root",
    "templates",
    "requirements",
}
DOCS_RECOMMENDED = [
    "docs/indice.md",
    "docs/ia/CONTEXT_HYGIENE.md",
    "docs/ia/ARCHITECTURE.md",
    "docs/ia/TESTING.md",
]

BODY_FIELD_ALIASES = {
    "contexto_funcional": {
        "contexto funcional",
        "contexto",
    },
    "tipo_cambio": {
        "tipo de cambio",
        "tipo",
    },
    "area_principal": {
        "area principal",
        "área principal",
        "area",
        "modulo principal",
        "módulo principal",
    },
    "resumen_changelog": {
        "resumen changelog",
        "resumen para changelog",
        "changelog",
    },
    "impacto_usuario": {
        "impacto usuario",
        "impacto para usuario",
    },
    "riesgos_rollback": {
        "riesgos rollback",
        "riesgos / rollback",
        "riesgos",
    },
    "pruebas_automaticas": {
        "pruebas automaticas",
        "pruebas automáticas",
    },
    "pruebas_manuales": {
        "pruebas manuales",
        "prubeas manuales",
    },
}

CHANGELOG_CATEGORY_LABELS = {
    "nuevas_funcionalidades": "Nuevas Funcionalidades",
    "actualizaciones": "Actualizaciones",
    "correccion_errores": "Corrección de Errores",
}


@dataclass
class PullRequestData:
    """Representa el contexto relevante de un pull request."""

    number: int
    title: str
    body: str
    html_url: str
    base_ref: str
    head_ref: str
    author: str
    updated_at: str
    repo_full_name: str


@dataclass
class PendingReleaseNote:
    """Modelo simple para release notes preliminares."""

    pr_number: int
    release_date: str
    category: str
    area: str
    title: str
    summary: str
    impact: str
    source_url: str


def slugify(value: str) -> str:
    """Convierte texto libre en un slug estable para nombres de archivo."""

    normalized = unicodedata.normalize("NFKD", value)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", ascii_text.lower()).strip("-")
    return slug or "sin-titulo"


def normalize_key(value: str) -> str:
    """Normaliza un label de metadata del body del PR."""

    normalized = unicodedata.normalize("NFKD", value)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii").lower()
    return re.sub(r"[^a-z0-9]+", " ", ascii_text).strip()


def clean_text(value: str) -> str:
    """Limpia texto libre para uso en Markdown generado."""

    collapsed = re.sub(r"\s+", " ", value or "").strip()
    return collapsed


def parse_pr_body_metadata(body: str) -> dict[str, str]:
    """Extrae metadata estructurada desde listas del body del PR."""

    metadata: dict[str, str] = {}
    for raw_line in (body or "").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if not line.startswith("-"):
            continue
        candidate = re.sub(r"^[\-\*\s]+", "", line)
        candidate = candidate.replace("**", "").replace("`", "")
        if ":" not in candidate:
            continue
        raw_key, raw_value = candidate.split(":", 1)
        normalized_key = normalize_key(raw_key)
        value = clean_text(raw_value)
        if not value:
            continue
        for canonical_key, aliases in BODY_FIELD_ALIASES.items():
            if normalized_key in aliases and canonical_key not in metadata:
                metadata[canonical_key] = value
                break
    return metadata


def next_wednesday(today: date) -> date:
    """Calcula el próximo miércoles, usando el mismo día si ya es miércoles."""

    days_until = (2 - today.weekday()) % 7
    return today + timedelta(days=days_until)


def remove_previous_pr_files(directory: Path, pattern: str) -> None:
    """Elimina archivos generados previos para un PR antes de recrearlos."""

    for stale_file in directory.glob(pattern):
        stale_file.unlink()


def detect_affected_areas(changed_files: list[str]) -> list[str]:
    """Resume áreas afectadas por el diff del PR."""

    detected: set[str] = set()
    for file_path in changed_files:
        parts = Path(file_path).parts
        if not parts:
            continue
        first = parts[0]
        if first in GENERIC_TOP_LEVEL:
            if first == "docs" and len(parts) > 1:
                detected.add(f"docs/{parts[1]}")
            elif first == ".github":
                detected.add(".github/workflows")
            else:
                detected.add(first)
            continue
        if len(parts) > 1 and parts[1] in {
            "views.py",
            "api_views.py",
            "services",
            "tests",
        }:
            detected.add(first)
            continue
        detected.add(first)
    return sorted(detected)


def collect_related_docs(changed_files: list[str]) -> list[str]:
    """Devuelve documentación relacionada que conviene mirar desde el PR."""

    docs = [path for path in changed_files if path.startswith("docs/")]
    related = DOCS_RECOMMENDED + docs
    deduplicated: list[str] = []
    for doc_path in related:
        if doc_path not in deduplicated:
            deduplicated.append(doc_path)
    return deduplicated


def build_architecture_notes(changed_files: list[str]) -> list[str]:
    """Genera notas arquitectónicas simples a partir de rutas tocadas."""

    notes: list[str] = []
    if any("/services/" in path for path in changed_files):
        notes.append(
            "El PR toca lógica en `services/`, por lo que impacta reglas de negocio u orquestación."
        )
    if any(path.endswith("api_views.py") or "/api_" in path for path in changed_files):
        notes.append(
            "Hay cambios en capa API/DRF y conviene revisar contratos de request/response."
        )
    if any(path.endswith("views.py") for path in changed_files):
        notes.append(
            "Hay cambios en vistas web y puede existir impacto en permisos o renderizado."
        )
    if any(
        "/templates/" in path or path.startswith("templates/") for path in changed_files
    ):
        notes.append(
            "Se modifican templates, con posible impacto visual o de composición UI."
        )
    if any(
        path.endswith("models.py") or "/migrations/" in path for path in changed_files
    ):
        notes.append(
            "Existen cambios de persistencia o migraciones que requieren revisión de datos."
        )
    if any(path.startswith(".github/") for path in changed_files):
        notes.append("El alcance incluye automatización o tooling de CI/CD.")
    if not notes:
        notes.append(
            "No se detectó un patrón arquitectónico dominante más allá del diff observado."
        )
    return notes


def build_design_system_notes(changed_files: list[str]) -> list[str]:
    """Resume impacto visual o de design system cuando aplica."""

    visual_files = [
        path
        for path in changed_files
        if path.startswith("templates/")
        or "/templates/" in path
        or path.startswith("static/")
        or path.endswith((".css", ".scss", ".js"))
    ]
    if not visual_files:
        return ["Sin cambios visibles de UI o design system detectados en el diff."]
    return [
        "El PR toca piezas de UI y conviene revisar consistencia visual con el patrón existente.",
        f"Archivos visuales relevantes: {', '.join(visual_files[:8])}",
    ]


def map_change_type_to_category(change_type: str) -> str:
    """Convierte el tipo de cambio del PR a una categoría del changelog."""

    normalized = normalize_key(change_type)
    if normalized in {"feat", "feature", "nueva funcionalidad", "funcionalidad"}:
        return CHANGELOG_CATEGORY_LABELS["nuevas_funcionalidades"]
    if normalized in {"fix", "bugfix", "hotfix", "correccion", "correccion de errores"}:
        return CHANGELOG_CATEGORY_LABELS["correccion_errores"]
    return CHANGELOG_CATEGORY_LABELS["actualizaciones"]


def sanitize_release_summary(summary: str, fallback_title: str) -> str:
    """Normaliza el resumen usado en release notes y changelog."""

    clean_summary = clean_text(summary)
    if clean_summary:
        return clean_summary.rstrip(".")
    return clean_text(fallback_title).rstrip(".")


def build_pr_document(
    pr: PullRequestData,
    metadata: dict[str, str],
    changed_files: list[str],
) -> str:
    """Genera el Markdown principal del PR."""

    areas = detect_affected_areas(changed_files)
    related_docs = collect_related_docs(changed_files)
    automatic_tests = metadata.get("pruebas_automaticas", "No informado en el PR.")
    manual_tests = metadata.get("pruebas_manuales", "No informado en el PR.")
    contexto = metadata.get(
        "contexto_funcional",
        "No informado explícitamente; revisar título, diff y documentación relacionada.",
    )
    riesgos = metadata.get(
        "riesgos_rollback",
        "No informado explícitamente en el PR.",
    )

    changed_files_block = (
        "\n".join(f"- `{path}`" for path in changed_files[:40])
        or "- Sin archivos detectados."
    )
    if len(changed_files) > 40:
        changed_files_block += (
            f"\n- ... y {len(changed_files) - 40} archivo(s) adicional(es) en el diff."
        )

    related_docs_block = "\n".join(f"- `{path}`" for path in related_docs)
    areas_block = (
        "\n".join(f"- `{area}`" for area in areas) or "- Sin áreas detectadas."
    )

    return f"""# PR #{pr.number} - {pr.title}

## Metadata

- PR: {pr.html_url}
- Base: `{pr.base_ref}`
- Rama origen: `{pr.head_ref}`
- Autor: `{pr.author}`
- Última actualización: `{pr.updated_at}`

## Resumen operativo

- Tipo de cambio: {metadata.get("tipo_cambio", "No informado")}
- Área principal: {metadata.get("area_principal", "No informada")}
- Contexto funcional: {contexto}
- Resumen para changelog: {metadata.get("resumen_changelog", "No informado")}
- Impacto usuario: {metadata.get("impacto_usuario", "No informado")}

## Áreas afectadas

{areas_block}

## Archivos relevantes del diff

{changed_files_block}

## Validación declarada

- Pruebas automáticas: {automatic_tests}
- Pruebas manuales: {manual_tests}

## Riesgos y rollback

- {riesgos}

## Documentación sugerida para lectura

{related_docs_block}

## Notas para continuidad

- Este documento es generado automáticamente desde el contexto del PR y sirve como índice rápido para revisión y futuras sesiones de agentes.
- Si la metadata del body del PR está incompleta, varias secciones usarán fallbacks derivados del título o del diff.
"""


def build_feature_context_document(
    pr: PullRequestData,
    metadata: dict[str, str],
    changed_files: list[str],
) -> str:
    """Genera el documento de contexto acumulable para agentes."""

    architecture_notes = "\n".join(
        f"- {note}" for note in build_architecture_notes(changed_files)
    )
    design_notes = "\n".join(
        f"- {note}" for note in build_design_system_notes(changed_files)
    )
    related_docs = "\n".join(
        f"- `{path}`" for path in collect_related_docs(changed_files)
    )
    important_files = "\n".join(f"- `{path}`" for path in changed_files[:20])
    if len(changed_files) > 20:
        important_files += f"\n- ... y {len(changed_files) - 20} archivo(s) adicional(es) relacionados."

    contexto = metadata.get(
        "contexto_funcional",
        "No informado explícitamente; inferir desde el título del PR y el diff.",
    )
    decisiones = [
        f"Tipo de cambio declarado: {metadata.get('tipo_cambio', 'No informado')}",
        f"Área principal declarada: {metadata.get('area_principal', 'No informada')}",
        f"Impacto usuario declarado: {metadata.get('impacto_usuario', 'No informado')}",
    ]
    decisiones_block = "\n".join(f"- {decision}" for decision in decisiones)

    return f"""# Contexto de feature PR #{pr.number} - {pr.title}

## Resumen

- PR: {pr.html_url}
- Base: `{pr.base_ref}`
- Rama origen: `{pr.head_ref}`
- Autor: `{pr.author}`

## Contexto funcional

- {contexto}

## Arquitectura tocada

{architecture_notes}

## Decisiones y supuestos detectados

{decisiones_block}
- Riesgos / rollback: {metadata.get('riesgos_rollback', 'No informado')}

## Design system y UI

{design_notes}

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-{pr.number}.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
{important_files or '- Sin archivos detectados.'}
- Documentación sugerida para ampliar contexto:
{related_docs}

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
"""


def build_pending_release_note(note: PendingReleaseNote) -> str:
    """Renderiza una release note preliminar en formato fácil de parsear."""

    return f"""---
pr: {note.pr_number}
release_date: {note.release_date}
category: {note.category}
area: {note.area}
title: {note.title}
summary: {note.summary}
impact: {note.impact}
source_url: {note.source_url}
---
# Release note preliminar PR #{note.pr_number}

- Fecha objetivo de release: {note.release_date}
- Categoría: {note.category}
- Área: {note.area}
- Título del PR: {note.title}
- Resumen: {note.summary}
- Impacto usuario: {note.impact}
- Fuente: {note.source_url}
"""


def parse_frontmatter(document: str) -> dict[str, str]:
    """Parsea el bloque simple de frontmatter generado por este script."""

    if not document.startswith("---\n"):
        return {}
    closing_index = document.find("\n---\n", 4)
    if closing_index == -1:
        return {}
    frontmatter = document[4:closing_index]
    parsed: dict[str, str] = {}
    for line in frontmatter.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        parsed[key.strip()] = value.strip()
    return parsed


def load_pending_release_notes(
    pending_dir: Path,
    release_date: str,
) -> list[PendingReleaseNote]:
    """Carga las notas pendientes de una release objetivo."""

    notes: list[PendingReleaseNote] = []
    for note_path in sorted(pending_dir.glob(f"{release_date}-pr-*.md")):
        parsed = parse_frontmatter(note_path.read_text(encoding="utf-8"))
        if not parsed:
            continue
        notes.append(
            PendingReleaseNote(
                pr_number=int(parsed["pr"]),
                release_date=parsed["release_date"],
                category=parsed["category"],
                area=parsed["area"],
                title=parsed["title"],
                summary=parsed["summary"],
                impact=parsed["impact"],
                source_url=parsed["source_url"],
            )
        )
    return notes


def build_release_changelog_block(
    release_date: str,
    notes: list[PendingReleaseNote],
) -> str:
    """Construye el bloque auto-generado del changelog para una release."""

    version_label = datetime.strptime(release_date, "%Y-%m-%d").strftime("%d.%m.%Y")
    grouped: dict[str, list[str]] = {
        label: [] for label in CHANGELOG_CATEGORY_LABELS.values()
    }
    for note in notes:
        bullet = f"- [{note.area}] {note.summary}. (PR #{note.pr_number})"
        grouped.setdefault(note.category, []).append(bullet)

    sections: list[str] = []
    for category in (
        CHANGELOG_CATEGORY_LABELS["nuevas_funcionalidades"],
        CHANGELOG_CATEGORY_LABELS["actualizaciones"],
        CHANGELOG_CATEGORY_LABELS["correccion_errores"],
    ):
        entries = grouped.get(category) or []
        if not entries:
            continue
        sections.append(f"## {category}\n\n" + "\n".join(entries))

    body = "\n\n".join(sections).strip()
    start_marker = AUTO_RELEASE_START.format(release_date=release_date)
    end_marker = AUTO_RELEASE_END.format(release_date=release_date)
    return (
        f"{start_marker}\n# Versión SISOC {version_label}\n\n{body}\n" f"{end_marker}\n"
    )


def replace_auto_release_block(
    changelog_content: str,
    release_date: str,
    replacement_block: str,
) -> str:
    """Reemplaza el bloque auto-generado de una release y preserva el resto."""

    pattern = re.compile(
        rf"{re.escape(AUTO_RELEASE_START.format(release_date=release_date))}\n.*?"
        rf"{re.escape(AUTO_RELEASE_END.format(release_date=release_date))}\n?",
        re.S,
    )
    without_block = pattern.sub("", changelog_content).lstrip()
    if without_block:
        return replacement_block + "\n" + without_block
    return replacement_block


def render_changelog(
    existing_content: str,
    release_date: str,
    notes: list[PendingReleaseNote],
) -> str:
    """Regenera el changelog para la release objetivo sin perder historial."""

    release_block = build_release_changelog_block(release_date, notes)
    return replace_auto_release_block(existing_content, release_date, release_block)


def read_event_payload(event_path: Path) -> dict[str, Any]:
    """Carga el payload del evento de GitHub."""

    return json.loads(event_path.read_text(encoding="utf-8"))


def extract_pull_request_data(payload: dict[str, Any]) -> PullRequestData:
    """Convierte el payload del evento a un objeto de trabajo."""

    pull_request = payload["pull_request"]
    repository = payload["repository"]
    return PullRequestData(
        number=int(pull_request["number"]),
        title=pull_request["title"],
        body=pull_request.get("body") or "",
        html_url=pull_request["html_url"],
        base_ref=pull_request["base"]["ref"],
        head_ref=pull_request["head"]["ref"],
        author=pull_request["user"]["login"],
        updated_at=pull_request["updated_at"],
        repo_full_name=repository["full_name"],
    )


def github_api_get_json(url: str, token: str) -> Any:
    """Hace una petición GET autenticada a la API de GitHub."""

    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "User-Agent": "sisoc-pr-doc-automation",
        },
    )
    with urllib.request.urlopen(request) as response:
        return json.loads(response.read().decode("utf-8"))


def fetch_changed_files(pr: PullRequestData, token: str) -> list[str]:
    """Obtiene la lista completa de archivos modificados del PR."""

    files: list[str] = []
    page = 1
    encoded_repo = urllib.parse.quote(pr.repo_full_name, safe="")
    while True:
        url = (
            "https://api.github.com/repos/"
            f"{encoded_repo}/pulls/{pr.number}/files?per_page=100&page={page}"
        )
        response_data = github_api_get_json(url, token)
        if not response_data:
            break
        files.extend(item["filename"] for item in response_data)
        if len(response_data) < 100:
            break
        page += 1
    return files


def ensure_parent_dirs() -> None:
    """Crea carpetas necesarias para artefactos generados."""

    DOCS_PR_DIR.mkdir(parents=True, exist_ok=True)
    DOCS_FEATURE_DIR.mkdir(parents=True, exist_ok=True)
    DOCS_RELEASE_PENDING_DIR.mkdir(parents=True, exist_ok=True)


def write_text_file(path: Path, content: str) -> None:
    """Escribe contenido UTF-8 normalizado en disco."""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def sync_pr_artifacts(
    pr: PullRequestData,
    token: str,
    today: date | None = None,
) -> None:
    """Genera todos los artefactos requeridos para un PR."""

    ensure_parent_dirs()
    changed_files = fetch_changed_files(pr, token)
    metadata = parse_pr_body_metadata(pr.body)

    pr_document_path = DOCS_PR_DIR / f"PR-{pr.number}.md"
    write_text_file(
        pr_document_path,
        build_pr_document(pr, metadata, changed_files),
    )

    remove_previous_pr_files(DOCS_FEATURE_DIR, f"pr-{pr.number}-*.md")
    feature_slug = slugify(pr.title)
    feature_context_path = DOCS_FEATURE_DIR / f"pr-{pr.number}-{feature_slug}.md"
    write_text_file(
        feature_context_path,
        build_feature_context_document(pr, metadata, changed_files),
    )

    if pr.base_ref != "main":
        return

    release_target = next_wednesday(today or date.today())
    release_file_date = release_target.strftime("%Y-%m-%d")
    remove_previous_pr_files(DOCS_RELEASE_PENDING_DIR, f"*-pr-{pr.number}.md")
    pending_note = PendingReleaseNote(
        pr_number=pr.number,
        release_date=release_file_date,
        category=map_change_type_to_category(metadata.get("tipo_cambio", "")),
        area=metadata.get("area_principal", "sin-area"),
        title=clean_text(pr.title),
        summary=sanitize_release_summary(
            metadata.get("resumen_changelog", ""),
            pr.title,
        ),
        impact=metadata.get("impacto_usuario", "No informado"),
        source_url=pr.html_url,
    )
    pending_path = DOCS_RELEASE_PENDING_DIR / f"{release_file_date}-pr-{pr.number}.md"
    write_text_file(pending_path, build_pending_release_note(pending_note))

    existing_changelog = ""
    if CHANGELOG_PATH.exists():
        existing_changelog = CHANGELOG_PATH.read_text(encoding="utf-8")
    notes = load_pending_release_notes(DOCS_RELEASE_PENDING_DIR, release_file_date)
    updated_changelog = render_changelog(existing_changelog, release_file_date, notes)
    write_text_file(CHANGELOG_PATH, updated_changelog)


def main() -> int:
    """Punto de entrada del script."""

    event_path_value = os.environ.get("GITHUB_EVENT_PATH")
    token = os.environ.get("GITHUB_TOKEN")
    if not event_path_value:
        raise RuntimeError("GITHUB_EVENT_PATH no está definido.")
    if not token:
        raise RuntimeError("GITHUB_TOKEN no está definido.")

    payload = read_event_payload(Path(event_path_value))
    pr = extract_pull_request_data(payload)
    try:
        sync_pr_artifacts(pr, token)
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"No se pudo consultar la API de GitHub: {exc}") from exc
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
