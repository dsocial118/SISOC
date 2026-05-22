# Memoria de contexto reutilizable para agentes

Fecha: 2026-04-16

## Que cambio

- Se agrego `scripts/ai/context_memory.py` para resolver memoria por path, detectar frescura contra `validated_commit`, crear plantillas nuevas y refrescar metadata.
- `scripts/ai/preflight.sh` ahora muestra memoria reutilizable antes de cerrar el arranque.
- Se agrego `scripts/ai/codex_context.ps1` y una accion nueva en `.codex/environments/environment.toml` para abrir la memoria desde Codex Desktop.
- Se creo `docs/contexto/memoria/` con README, plantilla y una memoria base del repo.
- Se actualizaron `AGENTS.md`, `CODEX.md`, `docs/indice.md`, `docs/ia/CONTEXT_HYGIENE.md` y `docs/operacion/codex_desktop.md` para incorporar el flujo.

## Impacto esperado

- Menos lecturas repetidas de codigo y docs estables.
- Mejor DX para asistentes y devs que arrancan tareas desde worktrees aisladas.
- Menor riesgo de usar memoria vieja porque cada documento declara commit y paths de invalidacion.

## Validacion prevista

- Tests unitarios del helper nuevo.
- Ejecucion manual de `preflight` y del wrapper PowerShell.
