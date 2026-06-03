# 2026-05-11 - Harness de agentes y validacion

## Contexto

El harness de agentes ya tenia guias, scripts Docker-first y CI suficiente, pero faltaba un comando unico de cierre y quedaban reglas duplicadas entre `AGENTS.md`, `docs/agentes/guia.md` y `.codex/rules.md`.

## Cambios aplicados

- Se agrego `scripts/ai/codex_run.ps1 validate` como validacion reproducible de cierre.
- Se compacto `AGENTS.md` para que sea mapa operativo y no enciclopedia.
- Se alinearon adaptadores y docs de agentes para evitar leer todas las guias de `docs/ia/` por defecto.
- Se expuso la validacion en Codex Desktop y en el preflight.
- Se documento como registrar errores repetidos de agentes en `docs/contexto/memoria/`.

## Impacto esperado

- Menos tokens de arranque por tarea.
- Menos errores por checkout viejo, worktree manual o dependencia de Python del host.
- Validacion mas facil de repetir antes de entregar cambios.

## Validacion

- `powershell -NoProfile -Command "$null = [scriptblock]::Create((Get-Content -Raw scripts/ai/codex_run.ps1))"`
- `powershell -ExecutionPolicy Bypass -File scripts/ai/codex_run.ps1 validate`
- `git diff --check`
- `Select-String -Path AGENTS.md,docs/agentes/guia.md,CODEX.md -Pattern 'docs/ia/\\*|docs/ia/*'`

## Riesgos y rollback

- Riesgo: `validate` puede ser mas lento que checks puntuales porque corre black, djlint, smoke y migraciones.
- Rollback: revertir este registro, los cambios en adaptadores/docs y la accion `validate` de `scripts/ai/codex_run.ps1`.
