"""Tests unitarios para la automatización de documentación de PR."""

import subprocess
from dataclasses import replace
from datetime import date
from pathlib import Path

from scripts.ci import pr_doc_automation


WORKFLOW_PATH = (
    Path(__file__).resolve().parents[1] / ".github/workflows/pr-docs.yml"
)


def test_pr_docs_workflow_detecta_artefactos_nuevos_no_trackeados():
    """No considera limpio el árbol cuando el generador crea los dos artefactos."""

    workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

    assert "pull_request:" in workflow
    assert "pull_request_target:" not in workflow
    assert "contents: read" in workflow
    assert "- development" in workflow
    assert "- homologacion" in workflow
    assert "- main" in workflow
    assert "git status --porcelain --untracked-files=all --" in workflow
    assert "git diff --quiet -- docs/registro/prs docs/contexto/features" not in workflow
    assert "generate_pr_artifacts:" in workflow
    assert "contents: write" in workflow
    assert (
        "head.repo.full_name == github.repository && "
        "github.event.pull_request.head.ref != 'development'"
    ) in workflow
    assert "Checkout base confiable del PR" in workflow
    assert "ref: ${{ github.event.pull_request.base.sha }}" in workflow
    assert "needs: generate_pr_artifacts" in workflow
    assert "if: always()" in workflow
    assert "refs/pull/${{ github.event.pull_request.number }}/head" in workflow
    assert "git ls-tree -r --name-only refs/remotes/origin/pr-head" in workflow
    assert "Faltan artefactos spec-as-source requeridos para mergear." in workflow
    assert "exit 1" in workflow


def test_git_status_detecta_los_artefactos_nuevos_que_git_diff_omite(tmp_path):
    """Reproduce el estado no trackeado que impedía el commit automático."""

    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    record_path = tmp_path / "docs/registro/prs/PR-2260.md"
    feature_path = (
        tmp_path / "docs/contexto/features/pr-2260-cdi-nomina-restriccion.md"
    )
    record_path.parent.mkdir(parents=True)
    feature_path.parent.mkdir(parents=True)
    record_path.write_text("registro\n", encoding="utf-8")
    feature_path.write_text("contexto\n", encoding="utf-8")

    diff = subprocess.run(
        [
            "git",
            "diff",
            "--quiet",
            "--",
            "docs/registro/prs",
            "docs/contexto/features",
        ],
        cwd=tmp_path,
        check=False,
    )
    status = subprocess.run(
        [
            "git",
            "status",
            "--porcelain",
            "--untracked-files=all",
            "--",
            "docs/registro/prs",
            "docs/contexto/features",
        ],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    )

    assert diff.returncode == 0
    assert "?? docs/registro/prs/PR-2260.md" in status.stdout
    assert "?? docs/contexto/features/pr-2260-cdi-nomina-restriccion.md" in status.stdout


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


def test_resolve_release_date_prioriza_fecha_explicita_del_pr():
    """Permite fijar el corte cuando el PR final declara fecha de release."""

    metadata = pr_doc_automation.parse_pr_body_metadata(
        "- Fecha objetivo de release: 2026-04-24"
    )

    explicit = pr_doc_automation.resolve_release_date(metadata, date(2026, 4, 24))
    fallback = pr_doc_automation.resolve_release_date({}, date(2026, 4, 24))

    assert explicit == "2026-04-24"
    assert fallback == "2026-04-29"


def test_resolve_release_date_ignora_fecha_explicita_invalida():
    """Usa fallback si el body trae un patron de fecha fuera de rango."""

    metadata = pr_doc_automation.parse_pr_body_metadata(
        "- Fecha objetivo de release: 2026-13-40"
    )

    assert pr_doc_automation.resolve_release_date(metadata, date(2026, 4, 24)) == (
        "2026-04-29"
    )


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


def test_sync_pr_artifacts_genera_los_dos_artefactos_para_pr_a_development(
    tmp_path, monkeypatch
):
    """Los PR a development también producen registro y contexto de feature."""

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

    pr = pr_doc_automation.PullRequestData(
        number=2260,
        title="Nomina CDI",
        body="",
        html_url="https://example.test/pr/2260",
        base_ref="development",
        head_ref="cdi_nomina_res",
        author="tester",
        updated_at="2026-08-10T13:00:00Z",
        repo_full_name="org/repo",
    )

    pr_doc_automation.sync_pr_artifacts(
        pr,
        token="fake-token",
        changed_files=["centrodesarrollo/views.py"],
    )

    assert (tmp_path / "docs/registro/prs/PR-2260.md").is_file()
    feature_files = list(
        (tmp_path / "docs/contexto/features").glob("pr-2260-*.md")
    )

    assert [path.name for path in feature_files] == [
        "pr-2260-nomina-cdi.md"
    ]
    assert not list((tmp_path / "docs/registro/releases/pending").glob("*.md"))
    assert not (tmp_path / "CHANGELOG.md").exists()


def test_sync_pr_artifacts_ignora_updated_at_para_evitar_autocommits_en_bucle(
    tmp_path, monkeypatch
):
    """Un push del bot no debe cambiar artefactos sólo por el timestamp del PR."""

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

    pr = pr_doc_automation.PullRequestData(
        number=2264,
        title="Documentar artefactos",
        body="",
        html_url="https://example.test/pr/2264",
        base_ref="development",
        head_ref="feature/docs",
        author="tester",
        updated_at="2026-08-10T17:41:37Z",
        repo_full_name="org/repo",
    )

    pr_doc_automation.sync_pr_artifacts(
        pr,
        token="fake-token",
        changed_files=[".github/workflows/pr-docs.yml"],
    )
    document_path = tmp_path / "docs/registro/prs/PR-2264.md"
    first_content = document_path.read_text(encoding="utf-8")

    pr_doc_automation.sync_pr_artifacts(
        replace(pr, updated_at="2026-08-10T18:35:35Z"),
        token="fake-token",
        changed_files=[".github/workflows/pr-docs.yml"],
    )

    assert document_path.read_text(encoding="utf-8") == first_content


def test_sync_pr_artifacts_mueve_pr_de_fecha_y_limpia_bloque_obsoleto(
    tmp_path, monkeypatch
):
    """Un cambio de fecha no debe dejar una release fantasma en el changelog."""

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

    stale_note = pr_doc_automation.PendingReleaseNote(
        pr_number=18,
        release_date="2026-03-25",
        category="Corrección de Errores",
        area="CI/CD",
        title="Hotfix de deploy",
        summary="Corrige el deploy anterior",
        impact="no",
        source_url="https://example.test/pr/18",
    )
    stale_pending = tmp_path / "docs/registro/releases/pending/2026-03-25-pr-18.md"
    stale_pending.parent.mkdir(parents=True, exist_ok=True)
    stale_pending.write_text(
        pr_doc_automation.build_pending_release_note(stale_note),
        encoding="utf-8",
    )
    (tmp_path / "CHANGELOG.md").write_text(
        pr_doc_automation.build_release_changelog_block("2026-03-25", [stale_note]),
        encoding="utf-8",
    )

    pr = pr_doc_automation.PullRequestData(
        number=18,
        title="Hotfix de deploy",
        body="- Fecha objetivo de release: 2026-03-18",
        html_url="https://example.test/pr/18",
        base_ref="main",
        head_ref="feature/hotfix-deploy",
        author="tester",
        updated_at="2026-03-13T12:00:00Z",
        repo_full_name="org/repo",
    )

    pr_doc_automation.sync_pr_artifacts(
        pr,
        token="fake-token",
        today=date(2026, 3, 13),
        changed_files=[".github/workflows/deploy.yml"],
    )

    changelog = (tmp_path / "CHANGELOG.md").read_text(encoding="utf-8")

    assert not stale_pending.exists()
    assert "2026-03-25" not in changelog
    assert "2026-03-18" in changelog


def test_manifest_de_diff_reemplaza_la_consulta_remota_de_archivos(
    tmp_path, monkeypatch
):
    """El pre-deploy documenta exactamente el diff que va a promover."""

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
        lambda pr, token: (_ for _ in ()).throw(
            AssertionError("no debe consultar API")
        ),
    )

    manifest = tmp_path / "changed-files.txt"
    manifest.write_text("core/views.py\n\ntemplates/core/home.html\n", encoding="utf-8")
    changed_files = pr_doc_automation.read_changed_files_file(manifest)
    pr = pr_doc_automation.PullRequestData(
        number=16,
        title="Preparar promocion con diff real",
        body="- Fecha objetivo de release: 2026-03-18",
        html_url="https://example.test/pr/16",
        base_ref="main",
        head_ref="development",
        author="tester",
        updated_at="2026-03-13T12:00:00Z",
        repo_full_name="org/repo",
    )

    pr_doc_automation.sync_pr_artifacts(
        pr,
        token="fake-token",
        today=date(2026, 3, 13),
        changed_files=changed_files,
    )

    generated = (tmp_path / "docs/registro/prs/PR-16.md").read_text(encoding="utf-8")
    assert "`core/views.py`" in generated
    assert "`templates/core/home.html`" in generated
