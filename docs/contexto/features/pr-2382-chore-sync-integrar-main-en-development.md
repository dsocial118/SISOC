# Contexto de feature PR #2382 - chore(sync): integrar main en development

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/2382
- Base: `development`
- Rama origen: `automation/sync-main-to-development`
- Autor: `sisoc-release-automation[bot]`

## Contexto funcional

- No informado explícitamente; inferir desde el título del PR y el diff.

## Arquitectura tocada

- Hay cambios en capa API/DRF y conviene revisar contratos de request/response.
- Existen cambios de persistencia o migraciones que requieren revisión de datos.

## Decisiones y supuestos detectados

- Tipo de cambio declarado: No informado
- Área principal declarada: No informada
- Impacto usuario declarado: No informado
- Riesgos / rollback: No informado

## Design system y UI

- Sin cambios visibles de UI o design system detectados en el diff.

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-2382.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `CHANGELOG.md`
- `comedores/api_views_territorial.py`
- `config/settings.py`
- `docs/contexto/features/pr-2380-feat-relevamientos-asignacion-por-usuario-territorial-corte-appsheet-por-flag.md`
- `docs/registro/prs/PR-2380.md`
- `docs/registro/releases/pending/2026-09-02-pr-2380.md`
- `relevamientos/migrations/0012_relevamiento_territorial_user.py`
- `relevamientos/models.py`
- `relevamientos/service.py`
- `tests/test_territorial_api.py`
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`
- `docs/contexto/features/pr-2380-feat-relevamientos-asignacion-por-usuario-territorial-corte-appsheet-por-flag.md`
- `docs/registro/prs/PR-2380.md`
- `docs/registro/releases/pending/2026-09-02-pr-2380.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
