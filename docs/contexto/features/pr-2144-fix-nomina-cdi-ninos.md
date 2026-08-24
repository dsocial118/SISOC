# Contexto de feature PR #2144 - Fix nomina cdi ninos

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/2144
- Base: `development`
- Rama origen: `fix_nominaCDINinos`
- Autor: `MariaNavarro90`

## Contexto funcional

- No informado explícitamente; inferir desde el título del PR y el diff.

## Arquitectura tocada

- Hay cambios en vistas web y puede existir impacto en permisos o renderizado.
- Se modifican templates, con posible impacto visual o de composición UI.
- Existen cambios de persistencia o migraciones que requieren revisión de datos.

## Decisiones y supuestos detectados

- Tipo de cambio declarado: No informado
- Área principal declarada: No informada
- Impacto usuario declarado: No informado
- Riesgos / rollback: No informado

## Design system y UI

- El PR toca piezas de UI y conviene revisar consistencia visual con el patrón existente.
- Archivos visuales relevantes: centrodeinfancia/templates/centrodeinfancia/destinatario_form.html, static/custom/js/destinatarioForm.js

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-2144.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `centrodeinfancia/forms.py`
- `centrodeinfancia/migrations/0042_alter_nominacentroinfancia_talla.py`
- `centrodeinfancia/models.py`
- `centrodeinfancia/templates/centrodeinfancia/destinatario_form.html`
- `centrodeinfancia/tests/test_centrodeinfancia_form.py`
- `centrodeinfancia/tests/test_destinatario_form.py`
- `centrodeinfancia/tests/test_destinatario_views.py`
- `centrodeinfancia/tests/test_nomina_edit_view.py`
- `centrodeinfancia/tests/test_nomina_integridad.py`
- `centrodeinfancia/tests/test_talla_migration.py`
- `centrodeinfancia/tests/test_trabajador_form.py`
- `core/validators.py`
- `docs/registro/cambios/2026-07-21-cdi-validaciones-nomina-nino.md`
- `static/custom/js/destinatarioForm.js`
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`
- `docs/registro/cambios/2026-07-21-cdi-validaciones-nomina-nino.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
