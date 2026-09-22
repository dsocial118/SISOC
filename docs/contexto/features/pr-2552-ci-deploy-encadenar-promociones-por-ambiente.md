# Contexto de feature PR #2552 - ci(deploy): encadenar promociones por ambiente

## Resumen

- PR: https://github.com/secretarianaf/SISOC/pull/2552
- Base: `main`
- Rama origen: `codex/satellite-ops`
- Autor: `dsocial118`

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
- Archivos visuales relevantes: .github/scripts/sync_main_downstream.js, .github/scripts/sync_main_downstream.test.js

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-2552.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `.github/scripts/sync_main_downstream.js`
- `.github/scripts/sync_main_downstream.test.js`
- `.github/workflows/deploy.yml`
- `.github/workflows/sync-main-downstream.yml`
- `AGENT_REPO_MAP.md`
- `CHANGELOG.md`
- `docs/contexto/features/pr-2552-ci-deploy-encadenar-promociones-por-ambiente.md`
- `docs/indice.md`
- `docs/operacion/deploy_automatizado.md`
- `docs/registro/cambios/2026-09-21-deploy-independiente-satelites.md`
- `docs/registro/prs/PR-2552.md`
- `docs/registro/releases/pending/2026-09-23-pr-2552.md`
- `scripts/operacion/deploy_verified.sh`
- `tests/test_deploy_workflow.py`
- Documentación sugerida para ampliar contexto:
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
