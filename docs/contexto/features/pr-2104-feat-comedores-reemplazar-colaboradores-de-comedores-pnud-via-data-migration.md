# Contexto de feature PR #2104 - feat(comedores): reemplazar colaboradores de comedores PNUD via data migration

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/2104
- Base: `development`
- Rama origen: `claude/issue-2099-analysis-plan-5e0537`
- Autor: `juanikitro`

## Contexto funcional

- Gestión de comedores / Colaboradores

## Arquitectura tocada

- El PR toca lógica en `services/`, por lo que impacta reglas de negocio u orquestación.
- Existen cambios de persistencia o migraciones que requieren revisión de datos.

## Decisiones y supuestos detectados

- Tipo de cambio declarado: Carga masiva de datos (data migration)
- Área principal declarada: comedores
- Impacto usuario declarado: Los colaboradores visibles en la PWA para comedores PNUD cambian según el nuevo listado.
- Riesgos / rollback: Migración no reversible (reverse=noop); validar reporte en HML antes de producción.

## Design system y UI

- Sin cambios visibles de UI o design system detectados en el diff.

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-2104.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `comedores/migrations/0048_replace_pnud_colaboradores.py`
- `comedores/migrations/data/colaboradores_pnud.csv`
- `comedores/services/pnud_colaboradores_migration.py`
- `tests/test_pnud_colaboradores_migration.py`
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
