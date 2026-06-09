# Contexto de feature PR #1864 - feat(relevamientos): badges Completado/Sincronizado en detalle y listado

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/1864
- Base: `main`
- Rama origen: `claude/awesome-taussig-ede43a`
- Autor: `juanikitro`

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
- Archivos visuales relevantes: relevamientos/templates/primer_seguimiento_detail.html, relevamientos/templates/relevamiento_detail.html, relevamientos/templates/relevamiento_list.html

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-1864.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `relevamientos/templates/primer_seguimiento_detail.html`
- `relevamientos/templates/relevamiento_detail.html`
- `relevamientos/templates/relevamiento_list.html`
- `relevamientos/views/web_views.py`
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
