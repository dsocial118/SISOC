# Codex runtime preflight

## Contexto

Las tareas de Codex en SISOC se demoraban por pasos repetidos de preparacion: crear worktree, generar `.env`, evitar choques de puertos y decidir si usar Python del host o Docker.

## Cambio

- Se agrega `scripts/ai/codex_task.ps1` para crear branch, worktree y bootstrap desde `origin/development`.
- Se agrega `docker-compose.codex.yml` para que el runtime de Codex no publique puertos por defecto.
- `scripts/ai/codex_run.ps1` ejecuta tests, linters y `manage.py` como contenedores one-off Docker-first.
- `scripts/ai/codex_bootstrap.ps1` acepta `-ExposePorts` para levantar una instancia navegable solo cuando hace falta.
- `docs/operacion/codex_desktop.md` queda como runbook operativo actualizado.

## Decision

Mantener el aislamiento por worktree como regla de seguridad y reducir el costo automatizando el preflight. El modo por defecto queda orientado a validacion y ejecucion paralela; la publicacion de puertos pasa a ser explicita para pruebas manuales.

## Validacion esperada

- `powershell -ExecutionPolicy Bypass -File scripts/ai/codex_bootstrap.ps1 -NoStart`
- `powershell -ExecutionPolicy Bypass -File scripts/ai/codex_doctor.ps1`
- `powershell -ExecutionPolicy Bypass -File scripts/ai/codex_run.ps1 black-check scripts/ai/context_memory.py --config pyproject.toml`
