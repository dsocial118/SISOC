from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DEPLOY_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "deploy.yml"


def _production_deploy_step() -> str:
    workflow = DEPLOY_WORKFLOW.read_text(encoding="utf-8")
    return workflow.split("    deploy-produccion:\n", maxsplit=1)[1]


def _qa_deploy_step() -> str:
    workflow = DEPLOY_WORKFLOW.read_text(encoding="utf-8")
    return workflow.split("    deploy-qa:\n", maxsplit=1)[1].split(
        "    deploy-homologacion:\n", maxsplit=1
    )[0]


def test_deploy_qa_actualiza_solo_development_antes_del_downtime():
    """Un ref remoto sin permisos no debe impedir el deploy de QA."""

    qa_step = _qa_deploy_step()
    scoped_fetch = (
        'git -C "$APP_ROOT" fetch origin --no-tags '
        'development:refs/remotes/origin/development'
    )
    fast_forward = 'git -C "$APP_ROOT" merge --ff-only origin/development'
    deploy_versioned = (
        './scripts/operacion/deploy_refresh.sh --yes --skip-pull '
        '--expected-revision "$EXPECTED_SHA"'
    )

    assert scoped_fetch in qa_step
    assert fast_forward in qa_step
    assert deploy_versioned in qa_step
    assert qa_step.index(scoped_fetch) < qa_step.index(fast_forward)
    assert qa_step.index(fast_forward) < qa_step.index(deploy_versioned)


def _legacy_talla_recovery_job() -> str:
    workflow = DEPLOY_WORKFLOW.read_text(encoding="utf-8")
    return workflow.split("    recuperar-talla-legacy-produccion:\n", maxsplit=1)[1]


def _legacy_talla_recovery_source(recovery_job: str) -> str:
    _, marker, remainder = recovery_job.partition("recovery=$'")
    assert marker
    source, marker, _ = remainder.partition("'\n                  docker compose")
    assert marker
    return bytes(source, "utf-8").decode("unicode_escape")


def test_deploy_produccion_inspeccion_legacy_no_contiene_escrituras():
    """El diagnóstico de talla legacy no debe conservar una ruta mutante."""

    recovery_job = _legacy_talla_recovery_job()
    recovery_source = _legacy_talla_recovery_source(recovery_job)

    assert "github.event_name == 'workflow_dispatch'" in recovery_job
    assert "environment: production" in recovery_job
    assert "runs-on: [self-hosted, sisoc-produccion]" in recovery_job
    assert 'remote_sha="$(git -C "$APP_ROOT" rev-parse origin/main)"' in recovery_job
    assert 'git -C "$APP_ROOT" cat-file -e "$EXPECTED_SHA^{commit}"' in recovery_job
    assert 'git -C "$APP_ROOT" archive --format=tar "$EXPECTED_SHA"' in recovery_job
    assert 'tar -x -C "$RECOVERY_ROOT"' in recovery_job
    assert 'ln -s "$APP_ROOT/.env" "$RECOVERY_ROOT/.env"' in recovery_job
    assert "trap cleanup_recovery EXIT" in recovery_job
    assert '--project-directory "$RECOVERY_ROOT"' in recovery_job
    assert "PROD_EXPECTED_DB_HOST" in recovery_job
    assert "PROD_EXPECTED_DB_SERVER" in recovery_job
    assert "PROD_EXPECTED_DB_NAME" in recovery_job
    assert "FOR UPDATE" not in recovery_job
    assert "transaction.atomic" not in recovery_job
    assert "UPDATE centrodeinfancia_nominacentroinfancia" not in recovery_job
    compile(recovery_source, "<legacy-talla-inspection>", "exec")
    assert "connection.ensure_connection()" in recovery_source
    assert "SELECT @@hostname, DATABASE()" in recovery_source
    assert "validate_database_identity()" in recovery_source
    assert "SELECT talla FROM centrodeinfancia_nominacentroinfancia" in recovery_source
    assert (
        'print(f"legacy_talla_id={record_id} category={categories[record_id]}")'
        in recovery_source
    )
    for mutation in ("INSERT ", "UPDATE ", "DELETE ", "ALTER ", "DROP "):
        assert mutation not in recovery_source


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
    # fmt: off
    healthcheck_end = production_step.index("\n                  fi\n", healthcheck_start)
    # fmt: on
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
