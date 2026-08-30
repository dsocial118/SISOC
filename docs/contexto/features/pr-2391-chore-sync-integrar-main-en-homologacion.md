# Contexto de feature PR #2391 - chore(sync): integrar main en homologacion

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/2391
- Base: `homologacion`
- Rama origen: `automation/sync-main-to-homologacion`
- Autor: `sisoc-release-automation[bot]`

## Contexto funcional

- No informado explícitamente; inferir desde el título del PR y el diff.

## Arquitectura tocada

- Hay cambios en capa API/DRF y conviene revisar contratos de request/response.

## Decisiones y supuestos detectados

- Tipo de cambio declarado: No informado
- Área principal declarada: No informada
- Impacto usuario declarado: No informado
- Riesgos / rollback: No informado

## Design system y UI

- Sin cambios visibles de UI o design system detectados en el diff.

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-2391.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `CHANGELOG.md`
- `comedores/api_views_territorial.py`
- `docs/contexto/features/pr-2389-fix-territorial-excluir-relevamientos-borrados-del-scope-por-asignacion.md`
- `docs/registro/prs/PR-2389.md`
- `docs/registro/releases/pending/2026-09-02-pr-2389.md`
- `tests/test_territorial_api.py`
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`
- `docs/contexto/features/pr-2389-fix-territorial-excluir-relevamientos-borrados-del-scope-por-asignacion.md`
- `docs/registro/prs/PR-2389.md`
- `docs/registro/releases/pending/2026-09-02-pr-2389.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
