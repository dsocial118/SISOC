from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DEPLOY_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "deploy.yml"


def _production_deploy_step() -> str:
    workflow = DEPLOY_WORKFLOW.read_text(encoding="utf-8")
    return workflow.split("    deploy-produccion:\n", maxsplit=1)[1]


def test_deploy_produccion_actualiza_helper_obsoleto_antes_del_deploy_versionado():
    """Un runner con helper previo debe poder alcanzar el deploy del SHA aprobado."""

    production_step = _production_deploy_step()
    remote_revision_check = 'remote_sha="$(git -C "$APP_ROOT" rev-parse origin/main)"'
    stale_helper_guard = (
        'if ! grep -q -- "--expected-revision" '
        '"$APP_ROOT/scripts/operacion/deploy_refresh.sh"; then'
    )
    main_branch_guard = '[[ "$(git -C "$APP_ROOT" branch --show-current)" == "main" ]]'
    fast_forward = 'git -C "$APP_ROOT" merge --ff-only origin/main'
    deploy_versioned = (
        './scripts/operacion/deploy_refresh.sh --yes --expected-revision '
        '"$EXPECTED_SHA" --with-mobile --mobile-dir /sisoc/SISOC-Mobile'
    )

    assert remote_revision_check in production_step
    assert stale_helper_guard in production_step
    assert main_branch_guard in production_step
    assert fast_forward in production_step
    assert deploy_versioned in production_step
    assert production_step.index(remote_revision_check) < production_step.index(
        stale_helper_guard
    )
    assert production_step.index(stale_helper_guard) < production_step.index(
        deploy_versioned
    )
    assert production_step.index(fast_forward) < production_step.index(deploy_versioned)
