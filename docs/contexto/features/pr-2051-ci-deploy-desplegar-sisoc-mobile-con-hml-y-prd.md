# Contexto de feature PR #2051 - ci(deploy): desplegar SISOC-Mobile con HML y PRD

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/2051
- Base: `main`
- Rama origen: `codex/prod-mobile-auto-deploy-20260714`
- Autor: `juanikitro`

## Contexto funcional

- Coordinar el deploy operativo de SISOC y SISOC-Mobile en HML y produccion desde el workflow existente.

## Arquitectura tocada

- El alcance incluye automatización o tooling de CI/CD.

## Decisiones y supuestos detectados

- Tipo de cambio declarado: actualizaciones
- Área principal declarada: infraestructura
- Impacto usuario declarado: Reduce el drift entre backend y frontend mobile durante los despliegues coordinados.
- Riesgos / rollback: El deploy combinado amplia el radio de impacto; no mergear fuera de la ventana. Ante fallo, recuperar primero las imagenes y commits registrados en el runbook PR #2049.

## Design system y UI

- Sin cambios visibles de UI o design system detectados en el diff.

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-2051.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `.github/workflows/deploy.yml`
- `CHANGELOG.md`
- `docs/contexto/features/pr-2051-ci-deploy-desplegar-sisoc-mobile-con-hml-y-prd.md`
- `docs/registro/prs/PR-2051.md`
- `docs/registro/releases/pending/2026-07-15-pr-2051.md`
- `scripts/operacion/deploy_refresh.sh`
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`
- `docs/contexto/features/pr-2051-ci-deploy-desplegar-sisoc-mobile-con-hml-y-prd.md`
- `docs/registro/prs/PR-2051.md`
- `docs/registro/releases/pending/2026-07-15-pr-2051.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
