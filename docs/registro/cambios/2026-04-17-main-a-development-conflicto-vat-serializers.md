# Merge main a development - conflicto en VAT serializers

Fecha: 2026-04-17

## Que cambio

- Se resolvio el conflicto de merge entre `origin/main` y `origin/development` en `VAT/serializers.py`.
- La resolucion conserva el refactor de validacion y alta automatica del postulante que ya estaba en `development`.
- Tambien conserva la correccion incorporada en `main` para completar `datos_postulante.documento` con el `documento` principal del request cuando ese dato no llega dentro del objeto del postulante.

## Decision manual

La fuente de verdad para el alta automatica del ciudadano sigue siendo la identidad normalizada del postulante, pero antes de esa normalizacion se completa el documento faltante desde el request principal.

Con esto, `development` absorbe el fix de `main` sin perder la estructura mas defensiva agregada en la rama de destino.

## Validacion

- `git merge --no-ff origin/main`
- `git diff --check`
- Revision manual del bloque resuelto en `VAT/serializers.py`

## Limites

- No se pudo correr el smoke test del entorno en esta worktree porque el bootstrap genero un `.env` invalido a partir de `.env.example` (linea 109 con claves comentadas como lista).
