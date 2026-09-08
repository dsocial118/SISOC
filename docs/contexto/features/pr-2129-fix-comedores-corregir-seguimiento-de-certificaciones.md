# Contexto de feature PR #2129 - fix(comedores): corregir seguimiento de certificaciones

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/2129
- Base: `development`
- Rama origen: `task/issue-1901-followup`
- Autor: `PabloCao1`

## Contexto funcional

- No informado explícitamente; inferir desde el título del PR y el diff.

## Arquitectura tocada

- Hay cambios en capa API/DRF y conviene revisar contratos de request/response.
- Hay cambios en vistas web y puede existir impacto en permisos o renderizado.
- Se modifican templates, con posible impacto visual o de composición UI.

## Decisiones y supuestos detectados

- Tipo de cambio declarado: No informado
- Área principal declarada: No informada
- Impacto usuario declarado: No informado
- Riesgos / rollback: No informado

## Design system y UI

- El PR toca piezas de UI y conviene revisar consistencia visual con el patrón existente.
- Archivos visuales relevantes: comedores/templates/comedor/certificaciones_prestaciones_historial.html, comedores/templates/comedor/comedor_detail.html

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-2129.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `AGENT_REPO_MAP.md`
- `comedores/api_views.py`
- `comedores/templates/comedor/certificaciones_prestaciones_historial.html`
- `comedores/templates/comedor/comedor_detail.html`
- `comedores/urls.py`
- `comedores/utils.py`
- `comedores/views/__init__.py`
- `comedores/views/comedor.py`
- `docs/registro/cambios/2026-07-21-issue-1901-seguimiento-certificaciones.md`
- `tests/test_certificacion_prestaciones_web.py`
- `tests/test_comedores_utils_unit.py`
- `tests/test_pwa_comedores_api.py`
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`
- `docs/registro/cambios/2026-07-21-issue-1901-seguimiento-certificaciones.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
