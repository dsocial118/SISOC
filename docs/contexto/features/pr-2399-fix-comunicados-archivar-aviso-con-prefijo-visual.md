# Contexto de feature PR #2399 - fix(comunicados): archivar aviso con prefijo visual

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/2399
- Base: `development`
- Rama origen: `codex/fix-cdi-comunicado-emoji`
- Autor: `juanikitro`

## Contexto funcional

- No informado explícitamente; inferir desde el título del PR y el diff.

## Arquitectura tocada

- Existen cambios de persistencia o migraciones que requieren revisión de datos.

## Decisiones y supuestos detectados

- Tipo de cambio declarado: No informado
- Área principal declarada: No informada
- Impacto usuario declarado: No informado
- Riesgos / rollback: No informado

## Design system y UI

- Sin cambios visibles de UI o design system detectados en el diff.

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-2399.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `comunicados/migrations/0012_rearchive_importacion_nomina_with_prefix.py`
- `docs/registro/cambios/2026-08-31-correccion-comunicado-importacion-nomina-hml.md`
- `tests/test_comunicados_migration_0010.py`
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`
- `docs/registro/cambios/2026-08-31-correccion-comunicado-importacion-nomina-hml.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
