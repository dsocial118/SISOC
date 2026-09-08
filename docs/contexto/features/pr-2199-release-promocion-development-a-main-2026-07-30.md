# Contexto de feature PR #2199 - release: promoción development a main 2026-07-30

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/2199
- Base: `main`
- Rama origen: `development`
- Autor: `juanikitro`

## Contexto funcional

- Promoción semanal de development a main con recuperación segura del bootstrap de deploy de producción.

## Arquitectura tocada

- El alcance incluye automatización o tooling de CI/CD.

## Decisiones y supuestos detectados

- Tipo de cambio declarado: Fix
- Área principal declarada: CI/CD
- Impacto usuario declarado: Sin cambio directo de interfaz; habilita la aplicación segura del SHA aprobado en producción.
- Riesgos / rollback: El bootstrap sólo avanza main mediante fast-forward tras validar el SHA remoto; rollback mediante el tag estable y PR nativo.

## Design system y UI

- Sin cambios visibles de UI o design system detectados en el diff.

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-2199.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `.github/workflows/deploy.yml`
- `tests/test_deploy_workflow.py`
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
