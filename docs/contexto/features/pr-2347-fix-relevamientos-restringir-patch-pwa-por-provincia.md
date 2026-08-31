# Contexto de feature PR #2347 - fix(relevamientos): restringir PATCH PWA por provincia

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/2347
- Base: `development`
- Rama origen: `codex/fix-pwa-territorial-idor`
- Autor: `juanikitro`

## Contexto funcional

- No informado explícitamente; inferir desde el título del PR y el diff.

## Arquitectura tocada

- Hay cambios en capa API/DRF y conviene revisar contratos de request/response.
- Hay cambios en vistas web y puede existir impacto en permisos o renderizado.

## Decisiones y supuestos detectados

- Tipo de cambio declarado: No informado
- Área principal declarada: No informada
- Impacto usuario declarado: No informado
- Riesgos / rollback: No informado

## Design system y UI

- Sin cambios visibles de UI o design system detectados en el diff.

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-2347.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `docs/registro/cambios/2026-08-26-pwa-territorial-idor.md`
- `relevamientos/views/api_views.py`
- `tests/test_relevamiento_api_patch.py`
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`
- `docs/registro/cambios/2026-08-26-pwa-territorial-idor.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
