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
        "./scripts/operacion/deploy_refresh.sh --yes --expected-revision "
        '"$EXPECTED_SHA" --with-mobile --mobile-dir /sisoc/SISOC-Mobile'
    )

    stale_helper_start = production_step.index(stale_helper_guard)
    stale_helper_end = production_step.index(
        "\n                  fi\n", stale_helper_start
    )
    deploy_start = production_step.index(deploy_versioned)
    stale_helper_block = production_step[stale_helper_start:stale_helper_end]

    assert remote_revision_check in production_step
    assert main_branch_guard in stale_helper_block
    assert fast_forward in stale_helper_block
    assert production_step.index(remote_revision_check) < stale_helper_start
    assert stale_helper_end < deploy_start
    assert stale_helper_block.index(main_branch_guard) < stale_helper_block.index(
        fast_forward
    )


def test_deploy_produccion_espera_migraciones_y_healthcheck_del_entrypoint():
    """Producción no debe fallar mientras el contenedor termina sus migraciones."""

    production_step = _production_deploy_step()
    deploy_versioned = (
        "./scripts/operacion/deploy_refresh.sh --yes --expected-revision "
        '"$EXPECTED_SHA" --with-mobile --mobile-dir /sisoc/SISOC-Mobile'
    )
    wait_for = "wait_for() {"
    diagnostics = "Diagnostico del servicio django de produccion"
    migrations = 'if ! wait_for "migraciones de produccion" 30 docker compose'
    healthcheck = (
        'if ! wait_for "healthcheck de produccion" 30 bash '
        '"$APP_ROOT/scripts/infra/healthcheck_prod.sh"'
    )

    assert diagnostics in production_step
    assert migrations in production_step
    assert healthcheck in production_step
    assert production_step.index(deploy_versioned) < production_step.index(wait_for)
    assert production_step.index(wait_for) < production_step.index(migrations)
    assert production_step.index(migrations) < production_step.index(healthcheck)

    healthcheck_start = production_step.index(healthcheck)
    healthcheck_end = production_step.index("\n                  fi\n", healthcheck_start)  # fmt: skip
    healthcheck_block = production_step[healthcheck_start:healthcheck_end]

    assert "show_django_diagnostics" in healthcheck_block
    assert "exit 1" in healthcheck_block


def test_deploy_produccion_solo_expone_inspeccion_legacy_de_lectura():
    """El rollback no debe dejar disponible una acción que altere datos productivos."""

    workflow = DEPLOY_WORKFLOW.read_text(encoding="utf-8")
    dispatch_inputs = workflow.split("workflow_dispatch:\n", maxsplit=1)[1].split(
        "\npermissions:", maxsplit=1
    )[0]
    recovery_job = workflow.split(
        "    recuperar-talla-legacy-produccion:\n", maxsplit=1
    )[1]

    assert "inspect-cdi-talla-blockers" in dispatch_inputs
    assert "repair-confirmed-cdi-talla-blockers-as-null" not in dispatch_inputs
    assert "inputs.maintenance_action == 'inspect-cdi-talla-blockers'" in recovery_job
    assert "FOR UPDATE" not in recovery_job
    assert "transaction.atomic" not in recovery_job
    assert "UPDATE centrodeinfancia_nominacentroinfancia" not in recovery_job
