#!/usr/bin/env python3
"""Render a server-context include; never install or reload Nginx."""

import argparse
from pathlib import Path

from deploy_pwas import configuration


def proxy(path, port):
    return f"""location ^~ {path} {{
    proxy_pass http://127.0.0.1:{port}/;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Forwarded-Host $host;
    proxy_set_header X-Forwarded-Port $server_port;
    proxy_redirect off;
}}
"""


def redirect_exact(source, target):
    return f"location = {source} {{ return 302 {target}$is_args$args; }}\n"


def render(apps, *, preview=False):
    parts = ["# Generated PWA locations. Include INSIDE the canonical HTTPS server.\n"]
    if preview:
        parts.append(
            "# PREVIEW ONLY: requires all web builds and legacy SW migration.\n"
        )
    for app in apps:
        if not app["enabled"] and not preview:
            parts.append(f"# {app['id']}: disabled; no upstream or alias exposed.\n")
            continue
        path = app["canonical_path"] if preview else app["base_path"]
        legacy = app["legacy_path"]
        if app["id"] == "espacios" and path != legacy and not preview:
            raise ValueError(
                "La migracion de /mobile/ requiere validar el service worker y "
                "los assets de instalaciones existentes antes de activar el include."
            )
        parts.append(redirect_exact(path.rstrip("/"), path))
        parts.append(proxy(path, app["port"]))
        if legacy != path:
            parts.append(redirect_exact(legacy.rstrip("/"), path))
            # Nginx rewrite appends the original query string automatically.
            parts.append(
                f"location ^~ {legacy} {{\n"
                f"    rewrite ^{legacy}(.*)$ {path}$1 redirect;\n"
                "}\n"
            )
        elif path != app["canonical_path"]:
            parts.append(f"# {app['canonical_path']} pending client migration.\n")
    return "\n".join(parts)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--preview", action="store_true")
    args = parser.parse_args()
    output = render(configuration(args.config), preview=args.preview)
    # Refuse overwrite: operator must explicitly choose a new candidate path.
    with args.output.open("x", encoding="utf-8", newline="\n") as target:
        target.write(output)


if __name__ == "__main__":
    main()
