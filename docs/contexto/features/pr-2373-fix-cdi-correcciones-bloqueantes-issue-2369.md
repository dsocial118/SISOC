# Contexto de feature PR #2373 - fix(cdi): correcciones bloqueantes issue 2369

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/2373
- Base: `development`
- Rama origen: `codex/issue-2369-correcciones-cdi`
- Autor: `juanikitro`

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
- Archivos visuales relevantes: centrodeinfancia/templates/centrodeinfancia/generar_usuario_egp.html, centrodeinfancia/templates/centrodeinfancia/usuario_egp_generado.html

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-2373.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `centrodeinfancia/access.py`
- `centrodeinfancia/forms.py`
- `centrodeinfancia/forms_formulario_cdi.py`
- `centrodeinfancia/forms_usuario_egp.py`
- `centrodeinfancia/formulario_cdi_schema.py`
- `centrodeinfancia/migrations/0046_alter_centrodeinfancia_fecha_inicio.py`
- `centrodeinfancia/models.py`
- `centrodeinfancia/services_user_provisioning.py`
- `centrodeinfancia/templates/centrodeinfancia/generar_usuario_egp.html`
- `centrodeinfancia/templates/centrodeinfancia/usuario_egp_generado.html`
- `centrodeinfancia/tests/test_automatic_user_provisioning.py`
- `centrodeinfancia/tests/test_centrodeinfancia_form.py`
- `centrodeinfancia/tests/test_destinatario_form.py`
- `centrodeinfancia/tests/test_generar_usuario_egp.py`
- `centrodeinfancia/tests/test_nomina_ninos_pdf.py`
- `centrodeinfancia/tests/test_trabajadores_views.py`
- `centrodeinfancia/views.py`
- `centrodeinfancia/views_export.py`
- `centrodeinfancia/views_usuario_egp.py`
- `docs/registro/2026-08-28-issue-2369-correcciones-cdi.md`
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`
- `docs/registro/2026-08-28-issue-2369-correcciones-cdi.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
