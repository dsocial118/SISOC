# CODEX.md

Instrucciones especificas para Codex en SISOC.

Fuente de verdad:
- `AGENTS.md`

Arranque minimo:
1. Leer `AGENTS.md`.
2. Leer `docs/indice.md`.
3. Leer archivo objetivo + tests del modulo.
4. Elegir una sola guia de `docs/ia/` segun la tarea.
5. Expandir solo si hace falta.

Usar:
- `docs/ia/CONTEXT_HYGIENE.md` para decidir que abrir,
- `scripts/ai/preflight.sh <tipo> [path]` para un resumen corto del contexto.

Fallback si `AGENTS.md` no esta disponible:
- no inventar contratos ni permisos,
- mantener diffs chicos,
- no mezclar feature con refactor amplio,
- agregar tests minimos cuando aplique,
- documentar cambios importantes en `docs/`.
