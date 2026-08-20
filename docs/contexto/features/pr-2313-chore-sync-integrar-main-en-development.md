# Contexto de feature PR #2313 - chore(sync): integrar main en development

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/2313
- Base: `development`
- Rama origen: `automation/sync-main-to-development`
- Autor: `sisoc-release-automation[bot]`

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
- Archivos visuales relevantes: centrodeinfancia/templates/centrodeinfancia/centrodeinfancia_list.html, centrodeinfancia/templates/centrodeinfancia/destinatario_detail.html, centrodeinfancia/templates/centrodeinfancia/destinatario_form.html, centrodeinfancia/templates/centrodeinfancia/nomina_form.html, centrodeinfancia/templates/centrodeinfancia/nomina_form_edit.html, centrodeinfancia/templates/centrodeinfancia/nomina_formulario_detail.html, static/custom/css/comedoresSearchBar.css, static/custom/js/destinatarioForm.js

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-2313.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `AGENT_REPO_MAP.md`
- `CHANGELOG.md`
- `centrodeinfancia/access.py`
- `centrodeinfancia/apps.py`
- `centrodeinfancia/forms.py`
- `centrodeinfancia/migrations/0044_nominacentroinfancia_departamento.py`
- `centrodeinfancia/models.py`
- `centrodeinfancia/services_nomina_ninos_pdf.py`
- `centrodeinfancia/templates/centrodeinfancia/centrodeinfancia_list.html`
- `centrodeinfancia/templates/centrodeinfancia/destinatario_detail.html`
- `centrodeinfancia/templates/centrodeinfancia/destinatario_form.html`
- `centrodeinfancia/templates/centrodeinfancia/nomina_form.html`
- `centrodeinfancia/templates/centrodeinfancia/nomina_form_edit.html`
- `centrodeinfancia/templates/centrodeinfancia/nomina_formulario_detail.html`
- `centrodeinfancia/tests/test_access_scope_centrodeinfancia.py`
- `centrodeinfancia/tests/test_automatic_user_provisioning.py`
- `centrodeinfancia/tests/test_destinatario_form.py`
- `centrodeinfancia/tests/test_nomina_ninos_pdf.py`
- `centrodeinfancia/tests/test_trabajador_form.py`
- `centrodeinfancia/tests/test_trabajadores_views.py`
- ... y 38 archivo(s) adicional(es) relacionados.
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`
- `docs/contexto/features/pr-2306-fix-cdi-resolver-urgentes-del-issue-2304.md`
- `docs/contexto/features/pr-2307-feat-centrodeinfancia-descargar-nomina-provincial-de-ninos-hml.md`
- `docs/contexto/features/pr-2308-feat-centrodeinfancia-descargar-nomina-provincial-de-ninos.md`
- `docs/contexto/features/pr-2310-fix-cdi-resolver-urgentes-del-issue-2304.md`
- `docs/contexto/features/pr-2311-fix-centrodeinfancia-asegurar-nomina-provincial-unica-hml.md`
- `docs/contexto/features/pr-2312-feat-centrodeinfancia-habilitar-descarga-superadmin-hml.md`
- `docs/contexto/features/pr-2313-chore-sync-integrar-main-en-development.md`
- `docs/plans/2026-08-18-issue-2304-urgentes-cdi-design.md`
- `docs/plans/2026-08-18-simepi-descarga-nomina-ninos-design.md`
- `docs/plans/2026-08-18-simepi-descarga-nomina-ninos-plan.md`
- `docs/plans/2026-08-18-simepi-superadmin-nomina-provincial-design.md`
- `docs/plans/2026-08-18-simepi-superadmin-nomina-provincial-plan.md`
- `docs/registro/cambios/2026-08-18-issue-2304-nomina-domicilio-sala.md`
- `docs/registro/cambios/2026-08-18-issue-2304-urgentes-cdi.md`
- `docs/registro/cambios/2026-08-18-simepi-descarga-nomina-ninos.md`
- `docs/registro/prs/PR-2306.md`
- `docs/registro/prs/PR-2307.md`
- `docs/registro/prs/PR-2308.md`
- `docs/registro/prs/PR-2310.md`
- `docs/registro/prs/PR-2311.md`
- `docs/registro/prs/PR-2312.md`
- `docs/registro/prs/PR-2313.md`
- `docs/registro/releases/pending/2026-08-19-pr-2308.md`
- `docs/registro/releases/pending/2026-08-26-pr-2310.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
