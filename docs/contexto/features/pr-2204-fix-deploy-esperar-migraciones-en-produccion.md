# Contexto de feature PR #2204 - fix(deploy): esperar migraciones en producción

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/2204
- Base: `main`
- Rama origen: `codex/fix-prod-migration-readiness-20260730`
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

- Sin cambios visibles de UI o design system detectados en el diff.

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-2204.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `.github/workflows/deploy.yml`
- `docs/operacion/deploy_automatizado.md`
- `docs/registro/cambios/2026-07-30-espera-migraciones-produccion.md`
- `tests/test_deploy_workflow.py`
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`
- `docs/operacion/deploy_automatizado.md`
- `docs/registro/cambios/2026-07-30-espera-migraciones-produccion.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
