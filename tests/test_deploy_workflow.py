from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DEPLOY_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "deploy.yml"
VERIFIED_DEPLOY = REPO_ROOT / "scripts" / "operacion" / "deploy_verified.sh"


def _workflow() -> str:
    return DEPLOY_WORKFLOW.read_text(encoding="utf-8")


def _job(name: str, next_name: str | None = None) -> str:
    source = _workflow().split(f"    {name}:\n", maxsplit=1)[1]
    if next_name:
        source = source.split(f"    {next_name}:\n", maxsplit=1)[0]
    return source


def test_qa_conserva_revision_previa_y_delega_rollback_verificado():
    qa = _job("deploy-qa", "deploy-homologacion")
    previous = 'previous_sha="$(git -C "$APP_ROOT" rev-parse HEAD)"'
    fast_forward = 'git -C "$APP_ROOT" merge --ff-only origin/development'
    verified = 'bash "$APP_ROOT/scripts/operacion/deploy_verified.sh"'

    assert qa.index(previous) < qa.index(fast_forward) < qa.index(verified)
    assert "--environment qa" in qa
    assert '--rollback-revision "$previous_sha"' in qa
    assert "--skip-pull" in qa


def test_hml_y_produccion_extraen_wrapper_del_sha_del_evento():
    for job, next_job, environment in (
        ("deploy-homologacion", "deploy-produccion", "homologacion"),
        ("deploy-produccion", "promover-produccion-a-homologacion", "production"),
    ):
        source = _job(job, next_job)
        validation = 'if [[ "$remote_sha" != "$EXPECTED_SHA" ]]'
        extraction = (
            'show "$EXPECTED_SHA:scripts/operacion/deploy_verified.sh" '
            '> "$deploy_script"'
        )
        execution = 'SISOC_ROOT_DIR="$APP_ROOT" bash "$deploy_script"'
        assert (
            source.index(validation)
            < source.index(extraction)
            < source.index(execution)
        )
        assert f"--environment {environment}" in source


def test_eventos_obsoletos_fallan_y_no_habilitan_promocion():
    for job, next_job in (
        ("deploy-qa", "deploy-homologacion"),
        ("deploy-homologacion", "deploy-produccion"),
        ("deploy-produccion", "promover-produccion-a-homologacion"),
    ):
        source = _job(job, next_job)
        obsolete = source.split(
            'if [[ "$remote_sha" != "$EXPECTED_SHA" ]]', maxsplit=1
        )[1].split("fi", maxsplit=1)[0]
        assert "exit 1" in obsolete
        assert "exit 0" not in obsolete


def test_wrapper_reconstruye_y_verifica_revision_anterior():
    script = VERIFIED_DEPLOY.read_text(encoding="utf-8")

    assert "trap rollback_on_exit EXIT" in script
    assert 'git -C "$ROOT_DIR" reset --hard "$previous_revision"' in script
    assert (
        '--skip-pull --expected-revision "$previous_revision" --without-mobile'
        in script
    )
    assert "if ! verify_stack; then" in script
    assert "Las migraciones de base de datos no se revierten automaticamente" in script


def test_promociones_usan_github_app_y_sha_desplegado():
    workflow = _workflow()
    for job, next_job, source, target in (
        (
            "promover-produccion-a-homologacion",
            "promover-homologacion-a-qa",
            "main",
            "homologacion",
        ),
        (
            "promover-homologacion-a-qa",
            "recuperar-talla-legacy-produccion",
            "homologacion",
            "development",
        ),
    ):
        promotion = _job(job, next_job)
        assert "actions/create-github-app-token@v3" in promotion
        assert "RELEASE_AUTOMATION_APP_CLIENT_ID" in promotion
        assert f"PROMOTION_SOURCE: {source}" in promotion
        assert f"PROMOTION_TARGET: {target}" in promotion
        assert "DEPLOYED_SHA: ${{ github.sha }}" in promotion
        assert "sync_main_downstream.js" in promotion


def _legacy_talla_recovery_job() -> str:
    return _job("recuperar-talla-legacy-produccion")


def _legacy_talla_recovery_source(recovery_job: str) -> str:
    _, marker, remainder = recovery_job.partition("recovery=$'")
    assert marker
    source, marker, _ = remainder.partition("'\n                  docker compose")
    assert marker
    return bytes(source, "utf-8").decode("unicode_escape")


def test_inspeccion_legacy_de_produccion_sigue_siendo_solo_lectura():
    recovery_job = _legacy_talla_recovery_job()
    recovery_source = _legacy_talla_recovery_source(recovery_job)

    assert "github.event_name == 'workflow_dispatch'" in recovery_job
    assert "environment: production" in recovery_job
    assert "runs-on: [self-hosted, sisoc-produccion]" in recovery_job
    assert 'git -C "$APP_ROOT" archive --format=tar "$EXPECTED_SHA"' in recovery_job
    assert "PROD_EXPECTED_DB_HOST" in recovery_job
    assert "FOR UPDATE" not in recovery_job
    assert "transaction.atomic" not in recovery_job
    compile(recovery_source, "<legacy-talla-inspection>", "exec")
    assert "SELECT @@hostname, DATABASE()" in recovery_source
    assert "SELECT talla FROM centrodeinfancia_nominacentroinfancia" in recovery_source
    for mutation in ("INSERT ", "UPDATE ", "DELETE ", "ALTER ", "DROP "):
        assert mutation not in recovery_source


def test_dispatch_no_expone_reparacion_mutante_de_talla():
    workflow = _workflow()
    dispatch_inputs = workflow.split("workflow_dispatch:\n", maxsplit=1)[1].split(
        "\npermissions:", maxsplit=1
    )[0]
    assert "inspect-cdi-talla-blockers" in dispatch_inputs
    assert "repair-confirmed-cdi-talla-blockers-as-null" not in dispatch_inputs
