## Codex Desktop: bootstrap y diagnostico de entorno

- Se agrego un flujo Docker-first para worktrees de Codex Desktop con `scripts/ai/codex_bootstrap.ps1`.
- El bootstrap ahora genera `.env` con puertos forward libres para reducir colisiones entre worktrees.
- Se agrego `scripts/ai/codex_run.ps1` como wrapper estable para tests, lint, formato, shell y comandos de Django dentro del contenedor `django`.
- Se agrego `scripts/ai/codex_doctor.ps1` para diagnosticar faltantes de `.env`, Docker, Compose, `py`, `black` y `pytest`.
- Se agrego `.codex/environments/environment.toml` para que Codex Desktop tenga setup y acciones utiles desde el repo.
- Se documento el flujo en `docs/operacion/codex_desktop.md` y se indexo en `docs/indice.md`.
