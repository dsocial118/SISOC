"""Tests unitarios para memoria operativa de contexto IA."""

from argparse import Namespace

from scripts.ai import context_memory


def write_memory_file(
    path,
    *,
    key="core",
    title="Core",
    summary="Resumen core",
    paths=None,
    default=False,
    confidence="alta",
    validated_commit="abc1234",
    validated_at="2026-04-16",
    body="# Core\n\n## Estado\n- Ok\n",
):
    """Escribe un documento de memoria valido para tests."""

    if paths is None:
        paths = ["core/"]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "+++",
                f'key = "{key}"',
                f'title = "{title}"',
                f'summary = "{summary}"',
                f"paths = {paths!r}".replace("'", '"'),
                f"default = {'true' if default else 'false'}",
                f'confidence = "{confidence}"',
                f'validated_commit = "{validated_commit}"',
                f'validated_at = "{validated_at}"',
                "+++",
                "",
                body,
            ]
        ),
        encoding="utf-8",
    )


def test_load_memory_document_parsea_frontmatter_y_cuerpo(tmp_path):
    """Lee metadata estructurada y preserva el cuerpo markdown."""

    memory_path = tmp_path / "core.md"
    write_memory_file(memory_path, paths=["core/", "tests/test_core_*.py"])

    document = context_memory.load_memory_document(memory_path, "versioned")

    assert document.key == "core"
    assert document.title == "Core"
    assert document.summary == "Resumen core"
    assert document.tracked_paths == ("core", "tests/test_core_*.py")
    assert document.validated_commit == "abc1234"
    assert document.confidence == "alta"
    assert document.body.startswith("# Core")


def test_path_pattern_matches_soporta_prefijos_y_globs():
    """Permite directorios y globs simples para resolver memoria."""

    assert context_memory.path_pattern_matches("core/", "core/views.py")
    assert context_memory.path_pattern_matches(
        "tests/test_core_*.py",
        "tests/test_core_views_unit.py",
    )
    assert not context_memory.path_pattern_matches("core/", "users/views.py")


def test_resolve_documents_prioriza_cache_local_e_incluye_defaults(
    tmp_path,
    monkeypatch,
):
    """Usa la memoria local si pisa la versionada y agrega la base default."""

    repo_root = tmp_path
    versioned_dir = repo_root / "docs/contexto/memoria"
    local_dir = repo_root / ".codex/cache/context-memory"
    write_memory_file(
        versioned_dir / "sisoc-base.md",
        key="sisoc-base",
        title="SISOC base",
        summary="Base",
        paths=["docs/"],
        default=True,
    )
    write_memory_file(
        versioned_dir / "core.md",
        key="core",
        summary="Versionada",
        paths=["core/"],
    )
    write_memory_file(
        local_dir / "core.md",
        key="core",
        summary="Local",
        paths=["core/"],
    )

    monkeypatch.setattr(context_memory, "REPO_ROOT", repo_root)
    monkeypatch.setattr(context_memory, "VERSIONED_MEMORY_DIR", versioned_dir)
    monkeypatch.setattr(context_memory, "LOCAL_MEMORY_DIR", local_dir)

    documents = context_memory.resolve_documents("core/views.py")

    assert [document.key for document in documents] == ["core", "sisoc-base"]
    assert documents[0].summary == "Local"


def test_evaluate_memory_status_devuelve_stale_si_hay_cambios(monkeypatch, tmp_path):
    """Marca la memoria como stale cuando cambian archivos seguidos."""

    document = context_memory.MemoryDocument(
        path=tmp_path / "core.md",
        key="core",
        title="Core",
        summary="Resumen",
        tracked_paths=("core/",),
        validated_commit="abc1234",
        validated_at="2026-04-16",
        confidence="alta",
        is_default=False,
        body="# Core\n",
        source="versioned",
    )

    monkeypatch.setattr(context_memory, "validated_commit_exists", lambda commit: True)
    monkeypatch.setattr(
        context_memory,
        "collect_relevant_changes",
        lambda doc: ("core/views.py",),
    )

    status = context_memory.evaluate_memory_status(document)

    assert status.state == "stale"
    assert status.changed_files == ("core/views.py",)


def test_command_scaffold_crea_memoria_versionada(tmp_path, monkeypatch, capsys):
    """Genera una plantilla inicial con metadata consistente."""

    repo_root = tmp_path
    versioned_dir = repo_root / "docs/contexto/memoria"
    monkeypatch.setattr(context_memory, "REPO_ROOT", repo_root)
    monkeypatch.setattr(context_memory, "VERSIONED_MEMORY_DIR", versioned_dir)
    monkeypatch.setattr(context_memory, "current_head_short", lambda: "4650322")

    args = Namespace(
        slug="core",
        title="Core",
        summary="Resumen operativo",
        paths=["core/", "tests/test_core_*.py"],
        confidence="alta",
        validated_commit=None,
        validated_at=None,
        default=False,
        local=False,
        force=False,
    )

    exit_code = context_memory.command_scaffold(args)
    output = capsys.readouterr().out.strip()
    created_file = versioned_dir / "core.md"

    assert exit_code == 0
    assert output == "docs/contexto/memoria/core.md"
    assert created_file.exists()
    content = created_file.read_text(encoding="utf-8")
    assert 'validated_commit = "4650322"' in content
    assert "# Core" in content


def test_command_refresh_preserva_cuerpo_y_actualiza_metadata(
    tmp_path,
    monkeypatch,
    capsys,
):
    """Refresca commit/fecha sin perder el cuerpo de la memoria."""

    repo_root = tmp_path
    versioned_dir = repo_root / "docs/contexto/memoria"
    memory_path = versioned_dir / "core.md"
    write_memory_file(memory_path, body="# Core\n\n## Estado\n- Sigue igual\n")

    monkeypatch.setattr(context_memory, "REPO_ROOT", repo_root)
    monkeypatch.setattr(context_memory, "VERSIONED_MEMORY_DIR", versioned_dir)
    monkeypatch.setattr(
        context_memory, "LOCAL_MEMORY_DIR", repo_root / ".codex/cache/context-memory"
    )
    monkeypatch.setattr(context_memory, "current_head_short", lambda: "9999999")

    args = Namespace(
        file="docs/contexto/memoria/core.md",
        validated_commit=None,
        validated_at="2026-04-20",
        summary="Resumen actualizado",
        confidence="media",
    )

    exit_code = context_memory.command_refresh(args)
    output = capsys.readouterr().out.strip()
    content = memory_path.read_text(encoding="utf-8")

    assert exit_code == 0
    assert output == "docs/contexto/memoria/core.md"
    assert 'validated_commit = "9999999"' in content
    assert 'validated_at = "2026-04-20"' in content
    assert 'summary = "Resumen actualizado"' in content
    assert "# Core" in content
    assert "- Sigue igual" in content
