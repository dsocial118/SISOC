# Contexto de feature PR #2297 - chore(sync): integrar main en development

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/2297
- Base: `development`
- Rama origen: `automation/sync-main-to-development`
- Autor: `sisoc-release-automation[bot]`

## Contexto funcional

- No informado explícitamente; inferir desde el título del PR y el diff.

## Arquitectura tocada

- Se modifican templates, con posible impacto visual o de composición UI.

## Decisiones y supuestos detectados

- Tipo de cambio declarado: No informado
- Área principal declarada: No informada
- Impacto usuario declarado: No informado
- Riesgos / rollback: No informado

## Design system y UI

- El PR toca piezas de UI y conviene revisar consistencia visual con el patrón existente.
- Archivos visuales relevantes: users/templates/user/_mi_cuenta_campos.html, users/templates/user/confirmar_datos.html, users/templates/user/mi_cuenta.html

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-2297.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `CHANGELOG.md`
- `admisiones/management/commands/corregir_expedientes_issue_2272.py`
- `admisiones/tests/test_corregir_expedientes_issue_2272.py`
- `docs/contexto/features/pr-2296-fix-admisiones-autorizar-transferencias-issue-2272.md`
- `docs/contexto/features/pr-2297-chore-sync-integrar-main-en-development.md`
- `docs/contexto/features/pr-2300-fix-users-quitar-declaracion-de-confirmacion-de-datos.md`
- `docs/operacion/correccion_expedientes_issue_2272.md`
- `docs/registro/cambios/2026-08-12-issue-2272-correccion-expedientes.md`
- `docs/registro/cambios/2026-08-14-confirmacion-datos-sin-declaracion.md`
- `docs/registro/prs/PR-2296.md`
- `docs/registro/prs/PR-2297.md`
- `docs/registro/prs/PR-2300.md`
- `docs/registro/releases/pending/2026-08-19-pr-2296.md`
- `docs/registro/releases/pending/2026-08-19-pr-2300.md`
- `tests/test_users_mi_cuenta.py`
- `users/forms.py`
- `users/templates/user/_mi_cuenta_campos.html`
- `users/templates/user/confirmar_datos.html`
- `users/templates/user/mi_cuenta.html`
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`
- `docs/contexto/features/pr-2296-fix-admisiones-autorizar-transferencias-issue-2272.md`
- `docs/contexto/features/pr-2297-chore-sync-integrar-main-en-development.md`
- `docs/contexto/features/pr-2300-fix-users-quitar-declaracion-de-confirmacion-de-datos.md`
- `docs/operacion/correccion_expedientes_issue_2272.md`
- `docs/registro/cambios/2026-08-12-issue-2272-correccion-expedientes.md`
- `docs/registro/cambios/2026-08-14-confirmacion-datos-sin-declaracion.md`
- `docs/registro/prs/PR-2296.md`
- `docs/registro/prs/PR-2297.md`
- `docs/registro/prs/PR-2300.md`
- `docs/registro/releases/pending/2026-08-19-pr-2296.md`
- `docs/registro/releases/pending/2026-08-19-pr-2300.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
