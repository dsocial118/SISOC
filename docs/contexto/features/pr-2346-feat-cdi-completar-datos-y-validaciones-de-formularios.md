# Contexto de feature PR #2346 - feat(cdi): completar datos y validaciones de formularios

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/2346
- Base: `development`
- Rama origen: `codex/issue-2342-cdi-forms`
- Autor: `juanikitro`

## Contexto funcional

- No informado explícitamente; inferir desde el título del PR y el diff.

## Arquitectura tocada

- Se modifican templates, con posible impacto visual o de composición UI.
- Existen cambios de persistencia o migraciones que requieren revisión de datos.

## Decisiones y supuestos detectados

- Tipo de cambio declarado: No informado
- Área principal declarada: No informada
- Impacto usuario declarado: No informado
- Riesgos / rollback: No informado

## Design system y UI

- El PR toca piezas de UI y conviene revisar consistencia visual con el patrón existente.
- Archivos visuales relevantes: centrodeinfancia/templates/centrodeinfancia/centrodeinfancia_form.html, centrodeinfancia/templates/centrodeinfancia/generar_usuario_cdi.html, centrodeinfancia/templates/centrodeinfancia/trabajador_form.html, static/custom/js/destinatarioForm.js, static/custom/js/trabajadorForm.js

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-2346.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `centrodeinfancia/forms.py`
- `centrodeinfancia/forms_generar_usuario.py`
- `centrodeinfancia/migrations/0045_centrodeinfancia_dni_cuil_referente.py`
- `centrodeinfancia/models.py`
- `centrodeinfancia/templates/centrodeinfancia/centrodeinfancia_form.html`
- `centrodeinfancia/templates/centrodeinfancia/generar_usuario_cdi.html`
- `centrodeinfancia/templates/centrodeinfancia/trabajador_form.html`
- `centrodeinfancia/tests/test_centrodeinfancia_form.py`
- `centrodeinfancia/tests/test_destinatario_form.py`
- `centrodeinfancia/tests/test_generar_usuario_cdi.py`
- `centrodeinfancia/tests/test_trabajador_form.py`
- `centrodeinfancia/views_usuario_cdi.py`
- `docs/registro/cambios/2026-08-25-issue-2342-cdi-forms.md`
- `static/custom/js/destinatarioForm.js`
- `static/custom/js/trabajadorForm.js`
- `users/services_generate_user.py`
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`
- `docs/registro/cambios/2026-08-25-issue-2342-cdi-forms.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
