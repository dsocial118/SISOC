"""Contrato estructural para que los CSV HTTP compartan la política UTF-8."""

import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CSV_POLICY_PATH = Path("core/services/csv_export.py")
CSV_INPUT_VALIDATOR_PATH = Path("insumos/validators.py")
LOCALIDADES_JS_EXPORT_PATH = Path("static/custom/js/localidades_modal.js")
ALLOWED_CSV_MIME_PATHS = {
    CSV_POLICY_PATH,
    CSV_INPUT_VALIDATOR_PATH,
    LOCALIDADES_JS_EXPORT_PATH,
}
CSV_MIME_LITERAL = re.compile(r"text/csv", flags=re.IGNORECASE)
SOURCE_SUFFIXES = {".py", ".js", ".ts", ".tsx"}


def test_exportadores_csv_http_reutilizan_la_politica_central():
    findings = []
    for path in PROJECT_ROOT.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in SOURCE_SUFFIXES:
            continue
        relative_path = path.relative_to(PROJECT_ROOT)
        if relative_path in ALLOWED_CSV_MIME_PATHS:
            continue
        if (
            "tests" in relative_path.parts
            or relative_path.name == "tests.py"
            or relative_path.name.startswith("test_")
            or "migrations" in relative_path.parts
        ):
            continue
        content = path.read_text(encoding="utf-8")
        if CSV_MIME_LITERAL.search(content):
            findings.append(str(relative_path))

    assert findings == [], (
        "Los responses CSV deben usar core.services.csv_export para aplicar "
        f"UTF-8 con BOM: {findings}"
    )


def test_exportador_javascript_existente_incluye_bom_utf8():
    content = (PROJECT_ROOT / LOCALIDADES_JS_EXPORT_PATH).read_text(encoding="utf-8")

    assert r'const BOM = "\uFEFF";' in content
    assert "let csv = BOM +" in content
    assert CSV_MIME_LITERAL.search(content)
