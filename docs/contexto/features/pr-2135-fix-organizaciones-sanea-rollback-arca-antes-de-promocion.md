# Contexto de feature PR #2135 - fix(organizaciones): sanea rollback ARCA antes de promoción

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/2135
- Base: `development`
- Rama origen: `codex/predeploy-dev-main-20260722`
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

- Empezar por `docs/registro/prs/PR-2135.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `CHANGELOG.md`
- `docs/contexto/features/pr-2136-release-promover-development-a-main-2026-07-22.md`
- `docs/registro/cambios/2026-07-22-predeploy-migracion-arca-rollback.md`
- `docs/registro/prs/PR-2136.md`
- `docs/registro/releases/pending/2026-07-22-pr-2136.md`
- `organizaciones/migrations/0016_issue_2083_documentacion_organizacion.py`
- `organizaciones/test_issue_2083_documentacion_organizacion.py`
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`
- `docs/contexto/features/pr-2136-release-promover-development-a-main-2026-07-22.md`
- `docs/registro/cambios/2026-07-22-predeploy-migracion-arca-rollback.md`
- `docs/registro/prs/PR-2136.md`
- `docs/registro/releases/pending/2026-07-22-pr-2136.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
