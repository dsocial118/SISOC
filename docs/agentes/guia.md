# Guia para asistentes (IA)

- Fuente de verdad: `AGENTS.md`.
- Arranque minimo: `AGENTS.md`, `docs/indice.md`, memoria aplicable, archivo objetivo, tests cercanos y una sola guia relevante de `docs/ia/`.
- No leer todas las guias de `docs/ia/` por defecto; ampliar contexto solo cuando haya evidencia concreta.
- Crear tareas no triviales con `scripts/ai/codex_task.ps1 <slug>` para trabajar desde `origin/development` en `../worktrees/<slug>`.
- Validar con `scripts/ai/codex_run.ps1 validate` cuando aplique; para Python modificado, sumar `scripts/ai/codex_run.ps1 pylint <archivo.py>`.
- Registrar cambios o decisiones importantes en `docs/registro/`; si ya existe documentacion del flujo tocado, actualizarla.
- Mantener diffs chicos, sin inventar modelos, endpoints, permisos, schemas ni dependencias.
- Commits generados por IA: mensaje en espanol con patron `<type>(<scope>): <subject>`; ver `docs/ia/CONTRIBUTING_AI.md`.
- Mejoras cercanas: proponerlas si ayudan, pero no implementarlas fuera de alcance sin aprobacion.
