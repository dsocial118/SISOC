+++
key = "sisoc-base"
title = "SISOC base IA"
summary = "Resumen operativo del repo para arrancar tareas IA con menos lecturas y sin perder boundaries."
paths = [
  "AGENTS.md",
  "CODEX.md",
  "docs/indice.md",
  "docs/ia/",
  "docs/operacion/codex_desktop.md",
  "scripts/ai/",
  ".codex/environments/environment.toml",
]
default = true
confidence = "alta"
validated_commit = "4650322e6"
validated_at = "2026-04-16"
+++

# SISOC base IA

## Estado
- Validada manualmente contra `AGENTS.md`, `docs/indice.md`, guias IA y helpers de `scripts/ai/`.
- Pensada como fast-path para arrancar antes de abrir modulos de dominio.

## Proposito
- El repo exige worktrees dedicadas desde `origin/development`.
- La lectura inicial debe ser minima y guiada por evidencia.
- `docs/` es fuente de verdad operativa y cualquier decision reusable debe registrarse.

## Entry points y archivos clave
- `AGENTS.md`: reglas duras de aislamiento, THINK, validacion y entrega.
- `CODEX.md`: arranque minimo y helpers recomendados para Codex.
- `docs/ia/CONTEXT_HYGIENE.md`: matriz de carga minima por tipo de tarea.
- `scripts/ai/preflight.sh`: resumen operativo corto por task kind.
- `scripts/ai/context_memory.py`: resuelve memoria reusable y detecta si quedo vieja.

## Patrones y contratos utiles
- La logica de negocio vive preferentemente en `services/`.
- Coexisten Django views y DRF; no asumir un unico boundary.
- Hay logging custom en `config/settings.py` y `core/utils.py`.
- No asumir Celery ni colas externas.

## Como validar rapido
- `bash scripts/ai/preflight.sh general`
- `python scripts/ai/context_memory.py preflight`
- `powershell -ExecutionPolicy Bypass -File scripts/ai/codex_context.ps1`

## Cuando invalidar esta memoria
- Si cambian `AGENTS.md`, `CODEX.md`, `docs/ia/`, `docs/operacion/codex_desktop.md` o `scripts/ai/`.
- Si cambia la politica de worktrees, tooling obligatorio o flujo de bootstrap.
