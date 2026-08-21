# Contexto de feature PR #2293 - chore(sync): integrar main en homologacion

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/2293
- Base: `homologacion`
- Rama origen: `automation/sync-main-to-homologacion`
- Autor: `sisoc-release-automation[bot]`

## Contexto funcional

- No informado explícitamente; inferir desde el título del PR y el diff.

## Arquitectura tocada

- Existen cambios de persistencia o migraciones que requieren revisión de datos.

## Decisiones y supuestos detectados

- Tipo de cambio declarado: No informado
- Área principal declarada: No informada
- Impacto usuario declarado: No informado
- Riesgos / rollback: No informado

## Design system y UI

- Sin cambios visibles de UI o design system detectados en el diff.

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-2293.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `CHANGELOG.md`
- `centrodeinfancia/forms.py`
- `centrodeinfancia/migrations/0042_alter_nominacentroinfancia_talla.py`
- `centrodeinfancia/migrations/0043_revert_nominacentroinfancia_talla_to_text.py`
- `centrodeinfancia/models.py`
- `centrodeinfancia/tests/test_destinatario_form.py`
- `centrodeinfancia/tests/test_talla_migration.py`
- `docs/contexto/features/pr-2210-revert-centrodeinfancia-restaurar-talla-legacy-como-texto.md`
- `docs/registro/cambios/2026-07-30-reversion-segura-talla-cdi.md`
- `docs/registro/prs/PR-2210.md`
- `docs/registro/releases/pending/2026-07-30-pr-2210.md`
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`
- `docs/contexto/features/pr-2210-revert-centrodeinfancia-restaurar-talla-legacy-como-texto.md`
- `docs/registro/cambios/2026-07-30-reversion-segura-talla-cdi.md`
- `docs/registro/prs/PR-2210.md`
- `docs/registro/releases/pending/2026-07-30-pr-2210.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
