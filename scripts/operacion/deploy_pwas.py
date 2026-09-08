#!/usr/bin/env python3
"""Prepare immutable PWA builds before SISOC downtime; activate after backend health.

Python stdlib only. Apps provide compose.yaml + compose.prod.yaml with a static
frontend image; disabled apps need neither checkout nor build dependencies.
"""

from __future__ import annotations

import argparse
import io
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys
import tarfile


REPOSITORIES = {
    "espacios": "dsocial118/Espacios-Comunitarios",
    "datacalle": "dsocial118/DataCalle",
    "gestionar": "dsocial118/Gestionar",
}


class DeployError(RuntimeError):
    """An actionable preflight or activation failure."""


def command(args, *, env=None, binary=False):
    """Never echo arguments or child output that may include build-time secrets."""
    result = subprocess.run(args, env=env, capture_output=True, check=False)
    if result.returncode:
        raise DeployError(
            f"{Path(str(args[0])).name} fallo (codigo {result.returncode}); "
            "revisar acceso/configuracion con el operador, sin volcar credenciales."
        )
    return result.stdout if binary else result.stdout.decode("utf-8").strip()


def save(path, value):
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    os.chmod(temporary, 0o600)
    temporary.replace(path)


def configuration(path):
    apps = json.loads(path.read_text(encoding="utf-8"))["apps"]
    seen = {key: set() for key in ("id", "checkout", "project", "port")}
    for app in apps:
        if app.get("repository") != REPOSITORIES.get(app.get("id")):
            raise DeployError("Repositorio PWA no permitido.")
        if type(app.get("enabled")) is not bool:
            raise DeployError("enabled debe ser un booleano explicito.")
        for key in ("id", "checkout", "project"):
            if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*", app[key]):
                raise DeployError(f"Identificador invalido: {key}")
        if type(app["port"]) is not int or not 1024 <= app["port"] <= 65535:
            raise DeployError("Puerto PWA invalido.")
        for key in seen:
            if app[key] in seen[key]:
                raise DeployError(f"Configuracion PWA duplicada: {key}")
            seen[key].add(app[key])
        for key in ("base_path", "canonical_path", "legacy_path"):
            if not re.fullmatch(r"/(?:[a-z0-9]+/)+", app[key]):
                raise DeployError(f"Ruta PWA invalida: {key}")
        if app.get("ssh_identity") is not None and not isinstance(
            app["ssh_identity"], str
        ):
            raise DeployError("Identidad SSH invalida.")
    return apps


def git_environment(app):
    env = os.environ.copy()
    env["GIT_TERMINAL_PROMPT"] = "0"
    env["GIT_ASKPASS"] = "/bin/false"
    env["GIT_SSH_COMMAND"] = "ssh -o BatchMode=yes -o StrictHostKeyChecking=yes"
    if app.get("ssh_identity"):
        identity = Path(app["ssh_identity"]).expanduser().resolve()
        if not identity.is_file():
            raise DeployError(f"{app['id']}: falta la identidad SSH del deploy.")
        env["GIT_SSH_COMMAND"] += " -o IdentitiesOnly=yes -i " + shlex.quote(
            str(identity)
        )
    return env


def snapshot(checkout, revision, destination):
    data = command(
        ["git", "-C", str(checkout), "archive", "--format=tar", revision],
        binary=True,
    )
    destination.mkdir(mode=0o700)
    with tarfile.open(fileobj=io.BytesIO(data)) as archive:
        for member in archive.getmembers():
            target = (destination / member.name).resolve()
            if destination.resolve() not in target.parents or not (
                member.isfile() or member.isdir()
            ):
                raise DeployError("El snapshot contiene enlaces o rutas no permitidos.")
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                source = archive.extractfile(member)
                if source is None:
                    raise DeployError("No se pudo leer un archivo del snapshot.")
                target.write_bytes(source.read())
                target.chmod(member.mode & 0o777)


def runtime_config(app, image):
    return {
        "services": {
            "frontend": {
                "image": image,
                "ports": [f"127.0.0.1:{app['port']}:8080"],
                "restart": "unless-stopped",
                "read_only": True,
                "cap_drop": ["ALL"],
                "security_opt": ["no-new-privileges:true"],
                "tmpfs": ["/tmp", "/var/cache/nginx"],
                "healthcheck": {
                    "test": [
                        "CMD-SHELL",
                        "wget -q -O /dev/null http://127.0.0.1:8080/ || exit 1",
                    ],
                    "interval": "5s",
                    "timeout": "3s",
                    "retries": 6,
                    "start_period": "10s",
                },
            }
        }
    }


def previous_container(app):
    ids = command(
        [
            "docker",
            "ps",
            "-aq",
            "--filter",
            f"label=com.docker.compose.project={app['project']}",
            "--filter",
            "label=com.docker.compose.service=frontend",
        ]
    ).splitlines()
    if len(ids) > 1:
        raise DeployError(f"{app['id']}: hay multiples contenedores frontend.")
    if not ids:
        return None
    container = json.loads(command(["docker", "inspect", ids[0]]))[0]
    if any(mount["Type"] in ("bind", "volume") for mount in container["Mounts"]):
        raise DeployError(f"{app['id']}: frontend con almacenamiento no contemplado.")
    return {"id": ids[0], "image": container["Image"]}


def compose_args(app, file):
    return ["docker", "compose", "--project-name", app["project"], "-f", str(file)]


def prepare(config, root, state_dir, environment):
    apps = [app for app in configuration(config) if app["enabled"]]
    state_file = state_dir / "state.json"
    if state_file.exists() or any((state_dir / app["id"]).exists() for app in apps):
        raise DeployError(
            "Usar un directorio de release nuevo; no sobrescribir estado."
        )
    state_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(state_dir, 0o700)
    state = {"environment": environment, "status": "preparing", "apps": []}
    save(state_file, state)
    # Resolve every enabled app before building or touching running services.
    for app in apps:
        checkout = (root / app["checkout"]).resolve()
        if root.resolve() not in checkout.parents or not (checkout / ".git").exists():
            raise DeployError(
                f"{app['id']}: falta un checkout provisionado dentro de root."
            )
        git = ["git", "-C", str(checkout)]
        if command(git + ["branch", "--show-current"]) != "main":
            raise DeployError(f"{app['id']}: el checkout debe estar en main.")
        if command(git + ["status", "--porcelain", "--untracked-files=no"]):
            raise DeployError(f"{app['id']}: checkout con cambios tracked.")
        # Fetch an explicit allowlisted URL; never rewrite an operator's origin.
        command(
            git
            + [
                "fetch",
                "--no-tags",
                f"git@github.com:{app['repository']}.git",
                "refs/heads/main",
            ],
            env=git_environment(app),
        )
        revision = command(git + ["rev-parse", "FETCH_HEAD^{commit}"])
        if not re.fullmatch(r"[0-9a-f]{40}", revision):
            raise DeployError("Revision PWA invalida.")
        command(git + ["merge-base", "--is-ancestor", "HEAD", revision])
        app_dir = state_dir / app["id"]
        app_dir.mkdir(mode=0o700)
        source = app_dir / "source"
        snapshot(checkout, revision, source)
        env_file = checkout / ".env"
        if not env_file.is_file():
            raise DeployError(f"{app['id']}: falta el .env local del entorno.")
        for name in ("compose.yaml", "compose.prod.yaml"):
            if not (source / name).is_file():
                raise DeployError(f"{app['id']}: falta {name} en main.")
        entry = dict(
            app, revision=revision, previous=previous_container(app), status="resolved"
        )
        entry["env_file"] = str(env_file)
        entry["image"] = f"{app['project']}-frontend:{environment}-{revision}"
        state["apps"].append(entry)
        save(state_file, state)
    for app in state["apps"]:
        print(f"[pwa] build {app['id']} main@{app['revision']}", flush=True)
        source = state_dir / app["id"] / "source"
        build = [
            "docker",
            "compose",
            "--project-name",
            app["project"],
            "--project-directory",
            str(source),
            "--env-file",
            app["env_file"],
            "-f",
            str(source / "compose.yaml"),
            "-f",
            str(source / "compose.prod.yaml"),
        ]
        env = os.environ.copy()
        env.update(
            IMAGE_TAG=f"{environment}-{app['revision']}",
            VITE_API_BASE_URL="/api",
            PWA_API_BASE_URL=(
                "https://hml-sisoc.secretarianaf.gob.ar/api"
                if environment == "hml"
                else "https://sisoc.secretarianaf.gob.ar/api"
            ),
            VITE_PUBLIC_BASE_PATH=app["base_path"],
            FRONTEND_BIND_ADDRESS="127.0.0.1",
            FRONTEND_PORT=str(app["port"]),
        )
        resolved = json.loads(command(build + ["config", "--format", "json"], env=env))
        if set(resolved["services"]) != {"frontend"}:
            raise DeployError(
                f"{app['id']}: se requiere solo el servicio frontend estatico."
            )
        if resolved["services"]["frontend"].get("image") != app["image"]:
            raise DeployError(f"{app['id']}: Compose no respeta la imagen versionada.")
        command(build + ["build", "frontend"], env=env)
        # Pin the actual image ID too: another build must not retarget activation.
        image_id = command(
            ["docker", "image", "inspect", "--format", "{{.Id}}", app["image"]]
        )
        if not re.fullmatch(r"sha256:[0-9a-f]{64}", image_id):
            raise DeployError("Docker no devolvio una imagen identificable.")
        app["image_id"] = image_id
        app["status"] = "built"
        save(state_dir / app["id"] / "runtime.json", runtime_config(app, image_id))
        save(state_file, state)
    state["status"] = "prepared"
    save(state_file, state)
    report(state)


def report(state):
    lines = [f"### PWA {state['environment']}: {state['status']}"]
    for app in state["apps"]:
        previous = (
            app["previous"]["image"] if app["previous"] else "sin version anterior"
        )
        lines.append(
            f"- {app['id']}: `{app['revision']}`; {app['status']}; anterior `{previous}`"
        )
    print("\n".join(lines), flush=True)
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as summary:
            summary.write("\n".join(lines) + "\n")


def activate(state_dir, environment):
    state_file = state_dir / "state.json"
    state = json.loads(state_file.read_text(encoding="utf-8"))
    if state["environment"] != environment or state["status"] != "prepared":
        raise DeployError("La release no esta preparada para este entorno.")
    # A competing/manual deploy invalidates rollback assumptions. Fail before activation.
    for app in state["apps"]:
        if previous_container(app) != app["previous"]:
            raise DeployError(
                f"{app['id']}: el contenedor cambio durante la preparacion."
            )
    state["status"] = "activating"
    save(state_file, state)
    for app in state["apps"]:
        runtime = state_dir / app["id"] / "runtime.json"
        compose = compose_args(app, runtime)
        try:
            command(
                compose
                + [
                    "up",
                    "-d",
                    "--no-build",
                    "--pull",
                    "never",
                    "--wait",
                    "--wait-timeout",
                    "90",
                    "frontend",
                ]
            )
            app["status"] = "healthy"
            save(state_file, state)
        except DeployError as error:
            app["status"] = "failed"
            if app["previous"]:
                rollback = state_dir / app["id"] / "rollback.json"
                save(rollback, runtime_config(app, app["previous"]["image"]))
                try:
                    command(
                        compose_args(app, rollback)
                        + [
                            "up",
                            "-d",
                            "--no-build",
                            "--pull",
                            "never",
                            "--wait",
                            "--wait-timeout",
                            "90",
                            "frontend",
                        ]
                    )
                    app["status"] = "rolled_back"
                except DeployError:
                    app["status"] = "rollback_failed"
            state["status"] = "failed_partial"
            save(state_file, state)
            report(state)
            raise DeployError(
                f"{app['id']}: {app['status']}; revisar state.json."
            ) from error
    state["status"] = "healthy"
    save(state_file, state)
    report(state)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("prepare", "activate"))
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument("--environment", choices=("hml", "prd"), required=True)
    parser.add_argument("--config", type=Path)
    parser.add_argument("--root", type=Path)
    args = parser.parse_args()
    try:
        if args.action == "prepare":
            if args.config is None or args.root is None:
                parser.error("prepare requiere --config y --root")
            prepare(args.config, args.root, args.state.resolve(), args.environment)
        else:
            activate(args.state.resolve(), args.environment)
    except (DeployError, OSError, ValueError, KeyError) as error:
        print(f"[pwa] ERROR: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
