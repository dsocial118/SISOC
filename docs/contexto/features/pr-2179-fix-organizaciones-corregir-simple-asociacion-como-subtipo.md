# Contexto de feature PR #2179 - fix(organizaciones): corregir Simple Asociación como subtipo

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/2179
- Base: `development`
- Rama origen: `codex/issue-2163-simple-asociacion`
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

- Empezar por `docs/registro/prs/PR-2179.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `docs/registro/cambios/2026-07-29-issue-2163-simple-asociacion.md`
- `organizaciones/fixtures/tipoentidad_subentidad.json`
- `organizaciones/migrations/0018_corregir_simple_asociacion_subtipo.py`
- `organizaciones/test_issue_2163_catalogo.py`
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`
- `docs/registro/cambios/2026-07-29-issue-2163-simple-asociacion.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
