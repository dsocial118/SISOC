# Contexto de feature PR #2205 - chore(sync): integrar main en development

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/2205
- Base: `development`
- Rama origen: `automation/sync-main-to-development`
- Autor: `sisoc-release-automation[bot]`

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

- Empezar por `docs/registro/prs/PR-2205.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `.github/workflows/deploy.yml`
- `AGENT_REPO_MAP.md`
- `CHANGELOG.md`
- `docs/contexto/features/pr-2204-fix-deploy-esperar-migraciones-en-produccion.md`
- `docs/operacion/deploy_automatizado.md`
- `docs/registro/cambios/2026-07-30-espera-migraciones-produccion.md`
- `docs/registro/prs/PR-2204.md`
- `docs/registro/releases/pending/2026-07-30-pr-2204.md`
- `scripts/ci/pr_doc_automation.py`
- `tests/test_deploy_workflow.py`
- `tests/test_pr_doc_automation_unit.py`
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`
- `docs/contexto/features/pr-2204-fix-deploy-esperar-migraciones-en-produccion.md`
- `docs/operacion/deploy_automatizado.md`
- `docs/registro/cambios/2026-07-30-espera-migraciones-produccion.md`
- `docs/registro/prs/PR-2204.md`
- `docs/registro/releases/pending/2026-07-30-pr-2204.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
