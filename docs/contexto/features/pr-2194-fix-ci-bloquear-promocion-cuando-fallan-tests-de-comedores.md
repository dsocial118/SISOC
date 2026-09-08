# Contexto de feature PR #2194 - fix(ci): bloquear promoción cuando fallan tests de Comedores

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/2194
- Base: `development`
- Rama origen: `codex/predeploy-dev-main-20260729-comedor-tests`
- Autor: `juanikitro`

## Contexto funcional

- No informado explícitamente; inferir desde el título del PR y el diff.

## Arquitectura tocada

- El alcance incluye automatización o tooling de CI/CD.

## Decisiones y supuestos detectados

- Tipo de cambio declarado: No informado
- Área principal declarada: No informada
- Impacto usuario declarado: No informado
- Riesgos / rollback: No informado

## Design system y UI

- El PR toca piezas de UI y conviene revisar consistencia visual con el patrón existente.
- Archivos visuales relevantes: .github/scripts/sync_main_downstream.test.js

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-2194.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `.github/scripts/sync_main_downstream.test.js`
- `.github/workflows/tests.yml`
- `docs/contexto/features/pr-2192-release-promover-development-a-main-2026-07-29.md`
- `docs/registro/prs/PR-2192.md`
- `tests/test_comedor_views_unit.py`
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`
- `docs/contexto/features/pr-2192-release-promover-development-a-main-2026-07-29.md`
- `docs/registro/prs/PR-2192.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
