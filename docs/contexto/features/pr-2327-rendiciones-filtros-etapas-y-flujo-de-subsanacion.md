# Contexto de feature PR #2327 - Rendiciones: filtros, etapas y flujo de subsanación

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/2327
- Base: `development`
- Rama origen: `Fixes-21-08`
- Autor: `PabloCao1`

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
- Archivos visuales relevantes: rendicioncuentasmensual/templates/rendicioncuentasmensual_detail.html, static/custom/css/main.css, static/custom/js/rendicioncuentasmensual_detail.js, templates/includes/base.html, templates/includes/sidebar/new_opciones.html, templates/includes/sidebar/opciones.html

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-2327.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `AGENT_REPO_MAP.md`
- `docs/contexto/features/pr-2327-rendiciones-filtros-etapas-y-flujo-de-subsanacion.md`
- `docs/registro/cambios/2026-08-21-filtro-estado-rendiciones.md`
- `docs/registro/cambios/2026-08-21-permisos-etapas-rendiciones.md`
- `docs/registro/prs/PR-2327.md`
- `rendicioncuentasmensual/filter_config.py`
- `rendicioncuentasmensual/forms.py`
- `rendicioncuentasmensual/management/__init__.py`
- `rendicioncuentasmensual/management/commands/__init__.py`
- `rendicioncuentasmensual/management/commands/seed_rendicion_stage_examples.py`
- `rendicioncuentasmensual/migrations/0018_stage_permissions.py`
- `rendicioncuentasmensual/models.py`
- `rendicioncuentasmensual/services.py`
- `rendicioncuentasmensual/templates/rendicioncuentasmensual_detail.html`
- `rendicioncuentasmensual/urls.py`
- `rendicioncuentasmensual/views.py`
- `static/custom/css/main.css`
- `static/custom/js/rendicioncuentasmensual_detail.js`
- `templates/includes/base.html`
- `templates/includes/sidebar/new_opciones.html`
- ... y 4 archivo(s) adicional(es) relacionados.
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`
- `docs/contexto/features/pr-2327-rendiciones-filtros-etapas-y-flujo-de-subsanacion.md`
- `docs/registro/cambios/2026-08-21-filtro-estado-rendiciones.md`
- `docs/registro/cambios/2026-08-21-permisos-etapas-rendiciones.md`
- `docs/registro/prs/PR-2327.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
