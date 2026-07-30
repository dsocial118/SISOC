# Contexto de feature PR #2207 - fix(deploy): recuperar tallas legacy bloqueantes

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/2207
- Base: `main`
- Rama origen: `codex/fix-prod-legacy-talla-20260730`
- Autor: `juanikitro`

## Contexto funcional

- Recuperar el deploy de producción preservando los datos legacy ambiguos hasta una acción explícita y auditada.

## Arquitectura tocada

- El alcance incluye automatización o tooling de CI/CD.

## Decisiones y supuestos detectados

- Tipo de cambio declarado: correccion
- Área principal declarada: CI/CD
- Impacto usuario declarado: Restaura la posibilidad de desplegar sin exponer ni inventar datos de personas.
- Riesgos / rollback: La acción mutante deja tres tallas inválidas en NULL; cualquier restauración exige fuente autorizada y auditoría.

## Design system y UI

- Sin cambios visibles de UI o design system detectados en el diff.

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-2207.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `.github/workflows/deploy.yml`
- `AGENT_REPO_MAP.md`
- `docs/operacion/deploy_automatizado.md`
- `docs/registro/cambios/2026-07-30-reparacion-controlada-talla-legacy-produccion.md`
- `tests/test_deploy_workflow.py`
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`
- `docs/operacion/deploy_automatizado.md`
- `docs/registro/cambios/2026-07-30-reparacion-controlada-talla-legacy-produccion.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
