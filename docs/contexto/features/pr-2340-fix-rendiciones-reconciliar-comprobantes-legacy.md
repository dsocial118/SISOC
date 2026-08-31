# Contexto de feature PR #2340 - fix(rendiciones): reconciliar comprobantes legacy

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/2340
- Base: `development`
- Rama origen: `codex/issue-2339-documentacion-reconciliation`
- Autor: `juanikitro`

## Contexto funcional

- conciliación de categorías de comprobantes entre SISOC y PWA.

## Arquitectura tocada

- Existen cambios de persistencia o migraciones que requieren revisión de datos.

## Decisiones y supuestos detectados

- Tipo de cambio declarado: migración de datos aditiva y documentación operativa.
- Área principal declarada: rendicioncuentasmensual.
- Impacto usuario declarado: evita documentos no visibles por categorías desalineadas.
- Riesgos / rollback: la reversa automática no es segura; rollback completo requiere restaurar el backup previo junto al código anterior.

## Design system y UI

- Sin cambios visibles de UI o design system detectados en el diff.

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-2340.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `docs/flujos/rendiciones_mensuales_proyectos.md`
- `docs/plans/2026-08-25-issue-2339-reconciliacion-documentos-design.md`
- `docs/registro/cambios/2026-08-25-issue-2339-reconciliacion-comprobantes.md`
- `rendicioncuentasmensual/migrations/0019_reconciliar_comprobantes_legacy.py`
- `tests/test_issue_2339_documentacion_adjunta_migration.py`
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`
- `docs/flujos/rendiciones_mensuales_proyectos.md`
- `docs/plans/2026-08-25-issue-2339-reconciliacion-documentos-design.md`
- `docs/registro/cambios/2026-08-25-issue-2339-reconciliacion-comprobantes.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
