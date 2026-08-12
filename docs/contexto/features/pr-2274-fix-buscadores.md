# Contexto de feature PR #2274 - Fix buscadores

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/2274
- Base: `development`
- Rama origen: `fix_buscadores`
- Autor: `MariaNavarro90`

## Contexto funcional

- No informado explícitamente; inferir desde el título del PR y el diff.

## Arquitectura tocada

- Se modifican templates, con posible impacto visual o de composición UI.

## Decisiones y supuestos detectados

- Tipo de cambio declarado: No informado
- Área principal declarada: No informada
- Impacto usuario declarado: No informado
- Riesgos / rollback: No informado

## Design system y UI

- El PR toca piezas de UI y conviene revisar consistencia visual con el patrón existente.
- Archivos visuales relevantes: celiaquia/templates/celiaquia/expediente_list.html, static/custom/css/poncho_listados.css, static/custom/js/poncho_scroll_tablas.js, templates/components/search_bar.html

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-2274.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `celiaquia/templates/celiaquia/expediente_list.html`
- `docs/contexto/features/pr-2274-fix-buscadores.md`
- `docs/registro/prs/PR-2274.md`
- `static/custom/css/poncho_listados.css`
- `static/custom/js/poncho_scroll_tablas.js`
- `templates/components/search_bar.html`
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`
- `docs/contexto/features/pr-2274-fix-buscadores.md`
- `docs/registro/prs/PR-2274.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
