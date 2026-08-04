# Contexto de feature PR #2139 - feat(release): automatizar promoción development a main

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/2139
- Base: `development`
- Rama origen: `codex/release-auto-merge-orchestration`
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
- Archivos visuales relevantes: .github/scripts/release_orchestrator.js, .github/scripts/release_orchestrator.test.js

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-2139.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `.gitattributes`
- `.github/pull_request_template.md`
- `.github/scripts/release_orchestrator.js`
- `.github/scripts/release_orchestrator.test.js`
- `.github/workflows/architecture.yml`
- `.github/workflows/deploy.yml`
- `.github/workflows/lint.yml`
- `.github/workflows/pr-docs.yml`
- `.github/workflows/release-orchestrator.yml`
- `.github/workflows/secrets.yml`
- `.github/workflows/sync-main-downstream.yml`
- `.github/workflows/tests.yml`
- `AGENT_REPO_MAP.md`
- `docs/operacion/deploy_automatizado.md`
- `docs/registro/cambios/2026-07-23-orquestacion-promocion-automatica.md`
- `docs/registro/decisiones/2026-07-23-promocion-automatica-con-tag-estable.md`
- `scripts/ci/pr_doc_automation.py`
- `scripts/operacion/deploy_refresh.sh`
- `tests/test_deploy_refresh_script.py`
- `tests/test_pr_doc_automation_unit.py`
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`
- `docs/operacion/deploy_automatizado.md`
- `docs/registro/cambios/2026-07-23-orquestacion-promocion-automatica.md`
- `docs/registro/decisiones/2026-07-23-promocion-automatica-con-tag-estable.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
