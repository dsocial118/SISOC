# Contexto de feature PR #2352 - feat(vat): buscar centros por CUE

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/2352
- Base: `development`
- Rama origen: `codex/vat-cue-lookup`
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

- Empezar por `docs/registro/prs/PR-2352.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `AGENT_REPO_MAP.md`
- `VAT/api_views.py`
- `VAT/serializers.py`
- `VAT/tests.py`
- `docs/plans/2026-08-26-vat-busqueda-centro-por-cue-design.md`
- `docs/registro/cambios/2026-08-26-vat-busqueda-centro-por-cue.md`
- `postman/Local.postman_environment.json`
- `postman/SISOC APIs.postman_collection.json`
- `postman/api_inventory.md`
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`
- `docs/plans/2026-08-26-vat-busqueda-centro-por-cue-design.md`
- `docs/registro/cambios/2026-08-26-vat-busqueda-centro-por-cue.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
