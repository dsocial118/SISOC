from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
INFRA_DIR = REPO_ROOT / "scripts" / "infra"


def test_infra_scripts_use_organization_runner_units_by_default():
    expected_defaults = {
        "healthcheck_prod.sh": (
            "actions.runner.secretarianaf.sisoc-produccion-org.service"
        ),
        "backup_prod_configs.sh": (
            "actions.runner.secretarianaf.sisoc-produccion-org.service"
        ),
        "backup_hml_configs.sh": (
            "actions.runner.secretarianaf.sisoc-homologacion-org.service"
        ),
        "backup_qa_configs.sh": "actions.runner.secretarianaf.sisoc-qa-org.service",
    }

    for script_name, expected_unit in expected_defaults.items():
        content = (INFRA_DIR / script_name).read_text(encoding="utf-8")
        assert expected_unit in content
        assert "actions.runner.dsocial118-SISOC" not in content


def test_runner_unit_defaults_keep_environment_override():
    expected_overrides = {
        "healthcheck_prod.sh": "PROD_RUNNER_UNIT",
        "backup_prod_configs.sh": "PROD_RUNNER_UNIT",
        "backup_hml_configs.sh": "HML_RUNNER_UNIT",
        "backup_qa_configs.sh": "QA_RUNNER_UNIT",
    }

    for script_name, variable_name in expected_overrides.items():
        content = (INFRA_DIR / script_name).read_text(encoding="utf-8")
        assert f"${{{variable_name}:-" in content
