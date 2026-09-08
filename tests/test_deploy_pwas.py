"""PWA orchestration tests without Docker, network, Django or live data."""

import importlib.util
import io
import json
from pathlib import Path
import tarfile

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "deploy_pwas", REPO_ROOT / "scripts/operacion/deploy_pwas.py"
)
deploy = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(deploy)
REVISION = "a" * 40
IMAGE_ID = "sha256:" + "b" * 64


def test_existing_service_identity_still_disables_interactive_ssh():
    env = deploy.git_environment({"ssh_identity": None})
    assert "BatchMode=yes" in env["GIT_SSH_COMMAND"]
    assert "StrictHostKeyChecking=yes" in env["GIT_SSH_COMMAND"]


def registry(tmp_path, count=1):
    apps = deploy.configuration(REPO_ROOT / "scripts/operacion/pwas.json")
    for index, app in enumerate(apps):
        app["enabled"] = index < count
        app["ssh_identity"] = None
        checkout = tmp_path / app["checkout"]
        if app["enabled"]:
            (checkout / ".git").mkdir(parents=True)
            (checkout / ".env").write_text("PRIVATE_MARKER=not-for-build-context\n")
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"apps": apps}))
    return path, apps


def archive():
    output = io.BytesIO()
    with tarfile.open(fileobj=output, mode="w") as tar:
        for name in ("compose.yaml", "compose.prod.yaml", "Dockerfile"):
            data = b"fixture"
            member = tarfile.TarInfo(name)
            member.size = len(data)
            tar.addfile(member, io.BytesIO(data))
    return output.getvalue()


class FakeCommands:
    def __init__(self, apps, *, fail_build=None, fail_start=None, previous=False):
        self.calls = []
        self.apps = apps
        self.fail_build = fail_build
        self.fail_start = fail_start
        self.previous = previous
        self.branch = "main"
        self.dirty = False
        self.changed = False

    def __call__(self, args, *, env=None, binary=False):
        self.calls.append((args, env))
        if args[0] == "git":
            action = args[3]
            if action == "branch":
                return self.branch
            if action == "status":
                return " M index.html" if self.dirty else ""
            if action == "fetch":
                return ""
            if action == "rev-parse":
                return REVISION
            if action == "merge-base":
                return ""
            if action == "archive":
                return archive()
            raise AssertionError(args)
        assert args[0] == "docker", args
        if args[1] == "ps":
            return "container" if self.previous else ""
        if args[1] == "inspect":
            return json.dumps(
                [
                    {
                        "Image": "old-changed" if self.changed else "old-image",
                        "Mounts": [],
                    }
                ]
            )
        if args[1:3] == ["image", "inspect"]:
            return IMAGE_ID
        assert args[1] == "compose", args
        project = args[args.index("--project-name") + 1]
        if "config" in args:
            return json.dumps(
                {
                    "services": {
                        "frontend": {"image": f"{project}-frontend:{env['IMAGE_TAG']}"}
                    }
                }
            )
        if "build" in args:
            if project == self.fail_build:
                raise deploy.DeployError("build fallo")
            return ""
        if "up" in args:
            if project == self.fail_start and args[args.index("-f") + 1].endswith(
                "runtime.json"
            ):
                raise deploy.DeployError("no saludable")
            return ""
        raise AssertionError(args)


def test_prepare_does_not_resolve_disabled_apps_or_start_services(
    tmp_path, monkeypatch
):
    config, apps = registry(tmp_path)
    fake = FakeCommands(apps)
    monkeypatch.setattr(deploy, "command", fake)
    deploy.prepare(config, tmp_path, tmp_path / "state", "hml")
    calls = [args for args, _ in fake.calls]
    fetches = [args for args in calls if "fetch" in args]
    assert len(fetches) == 1
    assert "git@github.com:dsocial118/Espacios-Comunitarios.git" in fetches[0]
    assert "refs/heads/main" in fetches[0]
    assert not any("up" in args or "down" in args for args in calls)
    assert not (tmp_path / "state/espacios/source/.env").exists()
    state = json.loads((tmp_path / "state/state.json").read_text())
    assert state["status"] == "prepared"
    assert state["apps"][0]["image_id"] == IMAGE_ID


@pytest.mark.parametrize("environment", ["hml", "prd"])
def test_all_three_build_from_main_before_any_activation(
    tmp_path, monkeypatch, environment
):
    monkeypatch.setenv("PWA_API_BASE_URL", "https://wrong-environment.invalid/api")
    config, apps = registry(tmp_path, count=3)
    fake = FakeCommands(apps)
    monkeypatch.setattr(deploy, "command", fake)
    deploy.prepare(config, tmp_path, tmp_path / "state", environment)
    before = len(fake.calls)
    deploy.activate(tmp_path / "state", environment)
    assert len([1 for args, _ in fake.calls[:before] if "fetch" in args]) == 3
    assert len([1 for args, _ in fake.calls[:before] if "build" in args]) == 3
    assert all(args[0] != "git" for args, _ in fake.calls[before:])
    for args, env in fake.calls:
        if "build" in args:
            assert env["IMAGE_TAG"] == f"{environment}-{REVISION}"
            assert env["VITE_API_BASE_URL"] == "/api"
            host = (
                "hml-sisoc.secretarianaf.gob.ar"
                if environment == "hml"
                else "sisoc.secretarianaf.gob.ar"
            )
            assert env["PWA_API_BASE_URL"] == f"https://{host}/api"
    assert (
        json.loads((tmp_path / "state/state.json").read_text())["status"] == "healthy"
    )


def test_build_failure_leaves_all_running_services_untouched(tmp_path, monkeypatch):
    config, apps = registry(tmp_path, count=3)
    fake = FakeCommands(apps, fail_build=apps[1]["project"])
    monkeypatch.setattr(deploy, "command", fake)
    with pytest.raises(deploy.DeployError):
        deploy.prepare(config, tmp_path, tmp_path / "state", "prd")
    assert not any("up" in args or "down" in args for args, _ in fake.calls)
    with pytest.raises(deploy.DeployError, match="no esta preparada"):
        deploy.activate(tmp_path / "state", "prd")


def test_failed_activation_rolls_back_only_failed_app_and_reports_partial(
    tmp_path, monkeypatch
):
    config, apps = registry(tmp_path, count=3)
    fake = FakeCommands(apps, previous=True, fail_start=apps[1]["project"])
    monkeypatch.setattr(deploy, "command", fake)
    deploy.prepare(config, tmp_path, tmp_path / "state", "hml")
    with pytest.raises(deploy.DeployError, match="rolled_back"):
        deploy.activate(tmp_path / "state", "hml")
    state = json.loads((tmp_path / "state/state.json").read_text())
    assert state["status"] == "failed_partial"
    assert [app["status"] for app in state["apps"]] == [
        "healthy",
        "rolled_back",
        "built",
    ]
    rollback = json.loads((tmp_path / "state/datacalle/rollback.json").read_text())
    assert rollback["services"]["frontend"]["image"] == "old-image"


def test_changed_container_blocks_activation_before_first_up(tmp_path, monkeypatch):
    config, apps = registry(tmp_path)
    fake = FakeCommands(apps, previous=True)
    monkeypatch.setattr(deploy, "command", fake)
    deploy.prepare(config, tmp_path, tmp_path / "state", "hml")
    fake.changed = True
    with pytest.raises(deploy.DeployError, match="contenedor cambio"):
        deploy.activate(tmp_path / "state", "hml")
    assert not any("up" in args for args, _ in fake.calls)


@pytest.mark.parametrize("problem", ["branch", "dirty"])
def test_bad_checkout_stops_before_build(tmp_path, monkeypatch, problem):
    config, apps = registry(tmp_path)
    fake = FakeCommands(apps)
    if problem == "branch":
        fake.branch = "development"
    else:
        fake.dirty = True
    monkeypatch.setattr(deploy, "command", fake)
    with pytest.raises(deploy.DeployError):
        deploy.prepare(config, tmp_path, tmp_path / "state", "hml")
    assert not any(args[0] == "docker" for args, _ in fake.calls)


def test_missing_identity_fails_without_interactive_credentials(tmp_path):
    with pytest.raises(deploy.DeployError, match="identidad SSH"):
        deploy.git_environment(
            {"id": "espacios", "ssh_identity": str(tmp_path / "missing")}
        )


def test_config_rejects_unknown_repository_and_duplicate_ports(tmp_path):
    config, apps = registry(tmp_path)
    apps[0]["repository"] = "other/Repository"
    config.write_text(json.dumps({"apps": apps}))
    with pytest.raises(deploy.DeployError, match="no permitido"):
        deploy.configuration(config)
    apps[0]["repository"] = deploy.REPOSITORIES["espacios"]
    apps[1]["port"] = apps[0]["port"]
    config.write_text(json.dumps({"apps": apps}))
    with pytest.raises(deploy.DeployError, match="duplicada"):
        deploy.configuration(config)


def test_snapshot_rejects_traversal(tmp_path, monkeypatch):
    output = io.BytesIO()
    with tarfile.open(fileobj=output, mode="w") as tar:
        member = tarfile.TarInfo("../escape")
        tar.addfile(member, io.BytesIO())
    monkeypatch.setattr(deploy, "command", lambda *a, **k: output.getvalue())
    with pytest.raises(deploy.DeployError, match="rutas no permitidos"):
        deploy.snapshot(tmp_path, REVISION, tmp_path / "source")
    assert not (tmp_path / "escape").exists()
