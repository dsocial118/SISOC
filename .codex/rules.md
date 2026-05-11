# Codex rules

Fuente de verdad: `AGENTS.md`.

- Usar `scripts/ai/codex_task.ps1 <slug>` para tareas no triviales y trabajar en `../worktrees/<slug>`.
- Cargar contexto minimo: `AGENTS.md`, `docs/indice.md`, memoria aplicable, archivo objetivo, tests cercanos y una sola guia de `docs/ia/`.
- No inventar APIs, modelos, endpoints, settings, permisos ni dependencias.
- Mantener diffs chicos y alineados con patrones existentes.
- Validar con `scripts/ai/codex_run.ps1 validate` cuando aplique; sumar checks puntuales si el cambio lo requiere.
- Registrar cambios o decisiones importantes en `docs/registro/`.
