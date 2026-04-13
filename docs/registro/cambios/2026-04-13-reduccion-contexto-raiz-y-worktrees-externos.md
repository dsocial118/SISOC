# Reduccion de contexto raiz y normalizacion de worktrees externos

Fecha: 2026-04-13

## Que cambio

- `AGENTS.md` se compacto para dejar una sola fuente de verdad corta.
- `CODEX.md`, `CLAUDE.md`, `LLM.md` y `.github/copilot-instructions.md` pasaron a ser adaptadores minimos en vez de duplicar reglas.
- La politica de lectura obligatoria cambio a "minimo contexto suficiente":
  - `AGENTS.md`
  - `docs/indice.md`
  - archivo objetivo
  - tests del modulo
  - una sola guia relevante de `docs/ia/`
- `docs/ia/CONTEXT_HYGIENE.md`, `docs/ia/CONTRIBUTING_AI.md`, `docs/agentes/guia.md`, `docs/registro/README.md`, `docs/operacion/codex_desktop.md` y `scripts/ai/preflight.sh` quedaron alineados a ese flujo.

## Politica vigente

- No se lee `docs/ia/*` completo por defecto.
- Se amplia contexto solo con evidencia concreta.
- Los worktrees nuevos deben vivir fuera del checkout principal, en `C:/Users/Juanito/Desktop/Repos-Codex/worktrees/<slug>`.
- `SISOC/.worktrees` queda obsoleto y no debe volver a usarse.

## Cambio operativo aplicado

- Se movieron los worktrees registrados dentro de `SISOC/.worktrees` al directorio externo `C:/Users/Juanito/Desktop/Repos-Codex/worktrees/`.
- El contenido remanente de esa carpeta se movio a `C:/Users/Juanito/Desktop/Repos-Codex/worktrees/legacy-dot-worktrees/`.
- Se elimino `SISOC/.worktrees` una vez vacio.

## Impacto esperado

- Menor costo fijo de tokens por turno.
- Menos ruido al explorar el repo.
- Menor riesgo de scope creep por lectura excesiva.
- Flujo de aislamiento consistente entre tareas nuevas y tareas existentes.
