# Contexto de feature PR #2490 - test(ci): corregir checks bloqueados en development

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/2490
- Base: `development`
- Rama origen: `codex/pr-2489-ci`
- Autor: `juanikitro`

## Contexto funcional

- No informado explícitamente; inferir desde el título del PR y el diff.

## Arquitectura tocada

- No se detectó un patrón arquitectónico dominante más allá del diff observado.

## Decisiones y supuestos detectados

- Tipo de cambio declarado: No informado
- Área principal declarada: No informada
- Impacto usuario declarado: No informado
- Riesgos / rollback: No informado

## Design system y UI

- Sin cambios visibles de UI o design system detectados en el diff.

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-2490.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `tests/test_importacion_codigo_postal_telefono.py`
- `tests/test_importacion_service_helpers_unit.py`
- `tests/test_legajo_editar_view_unit.py`
- `tests/test_rendicioncuentasmensual_services_unit.py`
- `tests/test_rendicioncuentasmensual_views_unit.py`
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
