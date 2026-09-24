# Contexto de feature PR #2572 - fix(deploy): desacoplar PWA del despliegue HML

## Resumen

- PR: https://github.com/secretarianaf/SISOC/pull/2572
- Base: `homologacion`
- Rama origen: `codex/hml-independent-deploy-20260924`
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

- Sin cambios visibles de UI o design system detectados en el diff.

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-2572.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `.github/workflows/deploy.yml`
- `AGENT_REPO_MAP.md`
- `docs/operacion/deploy_automatizado.md`
- `docs/operacion/deploy_pwas.md`
- `docs/registro/cambios/2026-09-24-desacople-deploy-hml-pwas.md`
- `tests/test_deploy_workflow.py`
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
