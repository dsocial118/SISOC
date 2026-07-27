# Contexto de feature PR #2127 - Fix cdi Primeros dos documentos

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/2127
- Base: `development`
- Rama origen: `Fix_cdi`
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
- Archivos visuales relevantes: centrodeinfancia/templates/centrodeinfancia/centrodeinfancia_form.html, centrodeinfancia/templates/centrodeinfancia/trabajador_form.html, static/custom/js/trabajadorForm.js

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-2127.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `centrodeinfancia/forms.py`
- `centrodeinfancia/migrations/0039_alter_trabajador_es_interprete_and_more.py`
- `centrodeinfancia/migrations/0040_trabajador_campos_verificados_renaper.py`
- `centrodeinfancia/migrations/0041_trabajador_fecha_actualizacion_and_more.py`
- `centrodeinfancia/models.py`
- `centrodeinfancia/templates/centrodeinfancia/centrodeinfancia_form.html`
- `centrodeinfancia/templates/centrodeinfancia/trabajador_form.html`
- `centrodeinfancia/tests/test_access_scope_centrodeinfancia.py`
- `centrodeinfancia/tests/test_automatic_user_provisioning.py`
- `centrodeinfancia/tests/test_centrodeinfancia_form.py`
- `centrodeinfancia/tests/test_trabajador_form.py`
- `centrodeinfancia/tests/test_trabajador_model.py`
- `centrodeinfancia/tests/test_trabajadores_views.py`
- `centrodeinfancia/views.py`
- `core/validators.py`
- `docs/registro/cambios/2026-07-14-cdi-validaciones-alta.md`
- `docs/registro/cambios/2026-07-16-cdi-validaciones-trabajador.md`
- `static/custom/js/trabajadorForm.js`
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`
- `docs/registro/cambios/2026-07-14-cdi-validaciones-alta.md`
- `docs/registro/cambios/2026-07-16-cdi-validaciones-trabajador.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
