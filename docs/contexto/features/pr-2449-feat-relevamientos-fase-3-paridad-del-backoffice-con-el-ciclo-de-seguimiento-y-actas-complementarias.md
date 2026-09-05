# Contexto de feature PR #2449 - feat(relevamientos): fase 3 - paridad del backoffice con el ciclo de seguimiento y actas complementarias

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/2449
- Base: `main`
- Rama origen: `pwanueva-v3`
- Autor: `Mkdir-arg`

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
- Archivos visuales relevantes: relevamientos/templates/acta_complementaria_detail.html, relevamientos/templates/acta_complementaria_form.html, relevamientos/templates/primer_seguimiento_detail.html, relevamientos/templates/relevamiento_detail.html, relevamientos/templates/relevamiento_list.html, relevamientos/templates/seguimiento_form.html

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-2449.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `CHANGELOG.md`
- `comedores/api_views_territorial.py`
- `comedores/tests.py`
- `comedores/views/relevamientos.py`
- `docs/contexto/features/pr-2449-feat-relevamientos-fase-3-paridad-del-backoffice-con-el-ciclo-de-seguimiento-y-actas-complementarias.md`
- `docs/registro/cambios/2026-09-05-fase3-backoffice-ciclo-seguimiento-y-actas.md`
- `docs/registro/prs/PR-2449.md`
- `docs/registro/releases/pending/2026-09-09-pr-2449.md`
- `relevamientos/forms_backoffice.py`
- `relevamientos/primer_seguimiento_service.py`
- `relevamientos/templates/acta_complementaria_detail.html`
- `relevamientos/templates/acta_complementaria_form.html`
- `relevamientos/templates/primer_seguimiento_detail.html`
- `relevamientos/templates/relevamiento_detail.html`
- `relevamientos/templates/relevamiento_list.html`
- `relevamientos/templates/seguimiento_form.html`
- `relevamientos/urls/web_urls.py`
- `relevamientos/views/backoffice_views.py`
- `relevamientos/views/seguimiento_helpers.py`
- `relevamientos/views/web_views.py`
- ... y 5 archivo(s) adicional(es) relacionados.
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`
- `docs/contexto/features/pr-2449-feat-relevamientos-fase-3-paridad-del-backoffice-con-el-ciclo-de-seguimiento-y-actas-complementarias.md`
- `docs/registro/cambios/2026-09-05-fase3-backoffice-ciclo-seguimiento-y-actas.md`
- `docs/registro/prs/PR-2449.md`
- `docs/registro/releases/pending/2026-09-09-pr-2449.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
