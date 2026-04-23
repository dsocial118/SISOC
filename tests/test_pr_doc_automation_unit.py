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


def test_normalize_changed_file_path_decodifica_paths_quoteados_por_git():
    """Normaliza rutas quoted con octales UTF-8 para que queden legibles."""

    raw_path = '"acompanamientos/templates/acompa\\303\\261amiento_detail.html"'

    assert (
        pr_doc_automation.normalize_changed_file_path(raw_path)
        == "acompanamientos/templates/acompañamiento_detail.html"
    )


def test_resolve_release_target_date_prioriza_fecha_del_pr():
    """Usa la fecha explícita del release cuando el PR ya la declara."""

    pr = pr_doc_automation.PullRequestData(
        number=1613,
        title="Release: development -> main (2026-04-23)",
        body="",
        html_url="https://example.test/pr/1613",
        base_ref="main",
        head_ref="development",
        author="tester",
        updated_at="2026-04-23T12:00:00Z",
        repo_full_name="org/repo",
    )

    resolved = pr_doc_automation.resolve_release_target_date(
        pr,
        metadata={},
        today=date(2026, 4, 24),
    )

    assert resolved == date(2026, 4, 23)


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


def test_fetch_changed_files_consulta_endpoint_de_pulls_sin_codificar_la_barra(
    monkeypatch,
):
    """Usa la ruta `/repos/{owner}/{repo}` que espera la API de GitHub."""

    requested_urls: list[str] = []

    def fake_github_api_get_json(url: str, token: str):
        requested_urls.append(url)
        return [{"filename": "core/views.py"}]

    monkeypatch.setattr(
        pr_doc_automation,
        "github_api_get_json",
        fake_github_api_get_json,
    )

    pr = pr_doc_automation.PullRequestData(
        number=15,
        title="Nueva automatizacion para PR",
        body="",
        html_url="https://example.test/pr/15",
        base_ref="development",
        head_ref="feature/pr-docs",
        author="tester",
        updated_at="2026-03-13T12:00:00Z",
        repo_full_name="org/repo",
    )

    changed_files = pr_doc_automation.fetch_changed_files(pr, token="fake-token")

    assert changed_files == ["core/views.py"]
    assert requested_urls == [
        "https://api.github.com/repos/org/repo/pulls/15/files?per_page=100&page=1"
    ]


def test_sync_pr_artifacts_respeta_fecha_del_release_declarada_en_el_pr(
    tmp_path, monkeypatch
):
    """Mantiene la fecha del release draft cuando el PR ya la hace explícita."""

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
        lambda pr, token: [
            '"acompanamientos/templates/acompa\\303\\261amiento_detail.html"'
        ],
    )

    pr = pr_doc_automation.PullRequestData(
        number=1613,
        title="Release: development -> main (2026-04-23)",
        body="""
        - Contexto funcional: Release train
        - Tipo de cambio: fix
        - Área principal: release
        - Resumen para changelog: Ajusta saneamientos del release
        """,
        html_url="https://example.test/pr/1613",
        base_ref="main",
        head_ref="development",
        author="tester",
        updated_at="2026-04-23T12:00:00Z",
        repo_full_name="org/repo",
    )

    pr_doc_automation.sync_pr_artifacts(pr, token="fake-token", today=date(2026, 4, 24))

    pending_files = list(
        (tmp_path / "docs/registro/releases/pending").glob("2026-04-23-pr-1613.md")
    )
    pr_doc = (tmp_path / "docs/registro/prs/PR-1613.md").read_text(encoding="utf-8")

    assert len(pending_files) == 1
    assert "acompañamiento_detail.html" in pr_doc


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
