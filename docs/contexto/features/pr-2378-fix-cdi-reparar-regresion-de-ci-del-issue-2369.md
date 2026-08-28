# Contexto de feature PR #2378 - fix(cdi): reparar regresión de CI del issue 2369

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/2378
- Base: `development`
- Rama origen: `codex/fix-cdi-ci-regression`
- Autor: `juanikitro`

## Contexto funcional

- No informado explícitamente; inferir desde el título del PR y el diff.

## Arquitectura tocada

- Hay cambios en vistas web y puede existir impacto en permisos o renderizado.
- Existen cambios de persistencia o migraciones que requieren revisión de datos.

## Decisiones y supuestos detectados

- Tipo de cambio declarado: No informado
- Área principal declarada: No informada
- Impacto usuario declarado: No informado
- Riesgos / rollback: No informado

## Design system y UI

- Sin cambios visibles de UI o design system detectados en el diff.

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-2378.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `centrodeinfancia/forms.py`
- `centrodeinfancia/migrations/0047_alter_formulariocdi_realiza_acciones_acompanamiento_vulneracion_derechos_and_more.py`
- `centrodeinfancia/tests/test_destinatario_views.py`
- `centrodeinfancia/tests/test_formulario_cdi_form.py`
- `centrodeinfancia/tests/test_formulario_cdi_views.py`
- `centrodeinfancia/tests/test_nomina_edit_view.py`
- `docs/registro/cambios/2026-08-28-cdi-reparacion-ci-2369.md`
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`
- `docs/registro/cambios/2026-08-28-cdi-reparacion-ci-2369.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
