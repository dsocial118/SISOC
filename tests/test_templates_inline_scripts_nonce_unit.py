"""Regresión liviana para CSP: scripts inline en templates deben incluir nonce."""

from pathlib import Path
import re


SCRIPT_TAG_RE = re.compile(r"<script\b(?P<attrs>[^>]*)>", re.IGNORECASE | re.DOTALL)


def _iter_repo_html_files():
    repo_root = Path(__file__).resolve().parents[1]
    excluded_path_parts = {
        ".venv",
        "node_modules",
        "site-packages",
        "coverage",
        "static_root",
    }
    for html_file in repo_root.rglob("*.html"):
        rel_path = html_file.relative_to(repo_root)
        if any(part in excluded_path_parts for part in rel_path.parts):
            continue
        yield rel_path, html_file


def test_all_inline_script_tags_have_nonce():
    missing_nonce = []
    for rel_path, html_file in _iter_repo_html_files():
        content = html_file.read_text(encoding="utf-8", errors="ignore")

        for match in SCRIPT_TAG_RE.finditer(content):
            attrs = match.group("attrs") or ""
            attrs_lower = attrs.lower()
            if "src=" in attrs_lower:
                continue
            if "nonce=" in attrs_lower:
                continue

            line = content.count("\n", 0, match.start()) + 1
            missing_nonce.append(f"{rel_path}:{line}")

    assert (
        missing_nonce == []
    ), "Se encontraron <script> inline sin nonce:\n" + "\n".join(missing_nonce)
