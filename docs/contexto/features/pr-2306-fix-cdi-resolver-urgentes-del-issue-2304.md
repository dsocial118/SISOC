# Contexto de feature PR #2306 - fix(cdi): resolver urgentes del issue 2304

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/2306
- Base: `homologacion`
- Rama origen: `codex/issue-2304-urgentes-cdi-main`
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
- Archivos visuales relevantes: centrodeinfancia/templates/centrodeinfancia/destinatario_detail.html, centrodeinfancia/templates/centrodeinfancia/destinatario_form.html, static/custom/js/destinatarioForm.js, static/custom/js/trabajadorForm.js, templates/includes/sidebar/opciones.html

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-2306.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `AGENT_REPO_MAP.md`
- `centrodeinfancia/access.py`
- `centrodeinfancia/apps.py`
- `centrodeinfancia/forms.py`
- `centrodeinfancia/templates/centrodeinfancia/destinatario_detail.html`
- `centrodeinfancia/templates/centrodeinfancia/destinatario_form.html`
- `centrodeinfancia/tests/test_access_scope_centrodeinfancia.py`
- `centrodeinfancia/tests/test_automatic_user_provisioning.py`
- `centrodeinfancia/tests/test_destinatario_form.py`
- `centrodeinfancia/tests/test_trabajador_form.py`
- `centrodeinfancia/tests/test_trabajadores_views.py`
- `comunicados/migrations/0010_archive_importacion_nomina.py`
- `docs/contexto/features/pr-2306-fix-cdi-resolver-urgentes-del-issue-2304.md`
- `docs/plans/2026-08-18-issue-2304-urgentes-cdi-design.md`
- `docs/registro/cambios/2026-08-18-issue-2304-urgentes-cdi.md`
- `docs/registro/prs/PR-2306.md`
- `iam/services.py`
- `static/custom/js/destinatarioForm.js`
- `static/custom/js/trabajadorForm.js`
- `templates/includes/sidebar/opciones.html`
- ... y 4 archivo(s) adicional(es) relacionados.
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`
- `docs/contexto/features/pr-2306-fix-cdi-resolver-urgentes-del-issue-2304.md`
- `docs/plans/2026-08-18-issue-2304-urgentes-cdi-design.md`
- `docs/registro/cambios/2026-08-18-issue-2304-urgentes-cdi.md`
- `docs/registro/prs/PR-2306.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
