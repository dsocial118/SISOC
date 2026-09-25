# Contexto de feature PR #2557 - Cambios

## Resumen

- PR: https://github.com/secretarianaf/SISOC/pull/2557
- Base: `development`
- Rama origen: `módulo-de-comunicados-#2505`
- Autor: `nehuen871`

## Contexto funcional

- No informado explícitamente; inferir desde el título del PR y el diff.

## Arquitectura tocada

- Hay cambios en vistas web y puede existir impacto en permisos o renderizado.
- Se modifican templates, con posible impacto visual o de composición UI.

## Decisiones y supuestos detectados

- Tipo de cambio declarado: No informado
- Área principal declarada: No informada
- Impacto usuario declarado: No informado
- Riesgos / rollback: No informado

## Design system y UI

- El PR toca piezas de UI y conviene revisar consistencia visual con el patrón existente.
- Archivos visuales relevantes: organizaciones/templates/organizacion_list.html, static/custom/css/comunicadoForm.css, static/custom/js/comunicadosDestinatarios.js, static/custom/js/comunicadosForm.js, templates/comunicados/comunicado_form.html, templates/comunicados/partials/destinatarios_panel.html

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-2557.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `comunicados/forms.py`
- `comunicados/services_destinatarios.py`
- `comunicados/urls.py`
- `comunicados/views.py`
- `docs/registro/cambios/2026-09-22-comunicados-seleccion-personalizada-destinatarios.md`
- `organizaciones/filter_config.py`
- `organizaciones/templates/organizacion_list.html`
- `organizaciones/views.py`
- `organizaciones/views_export.py`
- `static/custom/css/comunicadoForm.css`
- `static/custom/js/comunicadosDestinatarios.js`
- `static/custom/js/comunicadosForm.js`
- `templates/comunicados/comunicado_form.html`
- `templates/comunicados/partials/destinatarios_panel.html`
- `tests/test_comunicados_destinatarios_unit.py`
- `tests/test_organizaciones_filter_config_unit.py`
- `tests/test_organizaciones_views_unit.py`
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
