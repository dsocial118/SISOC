"""Tests unitarios para la automatización de documentación de PR."""

from datetime import date

from scripts.ci import pr_doc_automation


def test_parse_pr_body_metadata_extrae_campos_relevantes():
    """Extrae metadata estructurada desde la plantilla del PR."""

    body = """
    # Contexto

    - Contexto funcional: Permite cerrar una feature con trazabilidad automática.
    - Tipo de cambio: feature
    - Área principal: core
    - Resumen para changelog: Agrega documentación automática de PR y changelog
    - Impacto usuario: sí
    - Riesgos / rollback: Revertir workflow y scripts nuevos
    - Pruebas Automáticas: pytest tests/test_pr_doc_automation_unit.py
    - Prubeas Manuales: No aplica
    """

    metadata = pr_doc_automation.parse_pr_body_metadata(body)

    assert metadata["contexto_funcional"] == (
        "Permite cerrar una feature con trazabilidad automática."
    )
    assert metadata["tipo_cambio"] == "feature"
    assert metadata["area_principal"] == "core"
    assert metadata["resumen_changelog"] == (
        "Agrega documentación automática de PR y changelog"
    )
    assert metadata["impacto_usuario"] == "sí"
    assert metadata["riesgos_rollback"] == "Revertir workflow y scripts nuevos"
    assert metadata["pruebas_automaticas"] == (
        "pytest tests/test_pr_doc_automation_unit.py"
    )
    assert metadata["pruebas_manuales"] == "No aplica"


def test_detect_affected_areas_resume_apps_y_capas_transversales():
    """Resume áreas afectadas a partir del diff del PR."""

    changed_files = [
        "core/views.py",
        "comedores/services/sync.py",
        "docs/implementaciones/exportar_listados.md",
        ".github/workflows/tests.yml",
        "templates/core/home.html",
    ]

    areas = pr_doc_automation.detect_affected_areas(changed_files)

    assert ".github/workflows" in areas
    assert "comedores" in areas
    assert "core" in areas
    assert "docs/implementaciones" in areas
    assert "templates" in areas


def test_next_wednesday_devuelve_mismo_dia_si_ya_es_miercoles():
    """Usa el mismo día cuando la ejecución ya cae en miércoles."""

    same_day = pr_doc_automation.next_wednesday(date(2026, 3, 18))
    following = pr_doc_automation.next_wednesday(date(2026, 3, 13))

    assert same_day == date(2026, 3, 18)
    assert following == date(2026, 3, 18)


def test_render_changelog_reemplaza_bloque_auto_generado_de_misma_release(tmp_path):
    """Regenera el bloque auto y preserva el historial previo."""

    note = pr_doc_automation.PendingReleaseNote(
        pr_number=77,
        release_date="2026-03-18",
        category="Nuevas Funcionalidades",
        area="core",
        title="Agregar docs automáticas",
        summary="Agrega documentación automática del PR",
        impact="sí",
        source_url="https://example.test/pr/77",
    )
    pending_path = tmp_path / "2026-03-18-pr-77.md"
    pending_path.write_text(
        pr_doc_automation.build_pending_release_note(note),
        encoding="utf-8",
    )
    notes = pr_doc_automation.load_pending_release_notes(tmp_path, "2026-03-18")
    existing = """<!-- AUTO-GENERATED RELEASE START: 2026-03-18 -->
# Versión SISOC 18.03.2026

## Actualizaciones

- Texto viejo.
<!-- AUTO-GENERATED RELEASE END: 2026-03-18 -->

# Versión SISOC 04.03.2026

## Actualizaciones

- Release anterior.
"""

    changelog = pr_doc_automation.render_changelog(existing, "2026-03-18", notes)

    assert "Agrega documentación automática del PR" in changelog
    assert "Texto viejo." not in changelog
    assert "# Versión SISOC 04.03.2026" in changelog


def test_sync_pr_artifacts_genera_docs_y_changelog_para_pr_a_main(
    tmp_path, monkeypatch
):
    """Genera los artefactos esperados y elimina slugs previos del mismo PR."""

    monkeypatch.setattr(
        pr_doc_automation, "DOCS_PR_DIR", tmp_path / "docs/registro/prs"
    )
    monkeypatch.setattr(
        pr_doc_automation,
        "DOCS_FEATURE_DIR",
        tmp_path / "docs/contexto/features",
    )
    monkeypatch.setattr(
        pr_doc_automation,
        "DOCS_RELEASE_PENDING_DIR",
        tmp_path / "docs/registro/releases/pending",
    )
    monkeypatch.setattr(
        pr_doc_automation,
        "CHANGELOG_PATH",
        tmp_path / "CHANGELOG.md",
    )
    monkeypatch.setattr(
        pr_doc_automation,
        "fetch_changed_files",
        lambda pr, token: ["core/views.py", "templates/core/home.html"],
    )

    stale_feature = tmp_path / "docs/contexto/features/pr-15-nombre-viejo.md"
    stale_feature.parent.mkdir(parents=True, exist_ok=True)
    stale_feature.write_text("viejo", encoding="utf-8")

    pr = pr_doc_automation.PullRequestData(
        number=15,
        title="Nueva automatizacion para PR",
        body="""
        - Contexto funcional: Genera docs automáticas
        - Tipo de cambio: feature
        - Área principal: core
        - Resumen para changelog: Genera documentación de PR y changelog
        - Impacto usuario: no
        """,
        html_url="https://example.test/pr/15",
        base_ref="main",
        head_ref="feature/pr-docs",
        author="tester",
        updated_at="2026-03-13T12:00:00Z",
        repo_full_name="org/repo",
    )

    pr_doc_automation.sync_pr_artifacts(pr, token="fake-token", today=date(2026, 3, 13))

    pr_doc = (tmp_path / "docs/registro/prs/PR-15.md").read_text(encoding="utf-8")
    feature_files = list((tmp_path / "docs/contexto/features").glob("pr-15-*.md"))
    pending_files = list(
        (tmp_path / "docs/registro/releases/pending").glob("2026-03-18-pr-15.md")
    )
    changelog = (tmp_path / "CHANGELOG.md").read_text(encoding="utf-8")

    assert "Nueva automatizacion para PR" in pr_doc
    assert len(feature_files) == 1
    assert feature_files[0].name == "pr-15-nueva-automatizacion-para-pr.md"
    assert not stale_feature.exists()
    assert len(pending_files) == 1
    assert "Genera documentación de PR y changelog" in pending_files[0].read_text(
        encoding="utf-8"
    )
    assert "# Versión SISOC 18.03.2026" in changelog
    assert "Genera documentación de PR y changelog" in changelog
