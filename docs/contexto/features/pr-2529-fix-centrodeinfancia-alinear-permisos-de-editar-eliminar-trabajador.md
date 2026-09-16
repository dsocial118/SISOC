# Contexto de feature PR #2529 - fix(centrodeinfancia): alinear permisos de editar/eliminar trabajador

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/2529
- Base: `development`
- Rama origen: `fix/issue-2528-permisos-trabajadores-cdi`
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
- Archivos visuales relevantes: centrodeinfancia/templates/centrodeinfancia/trabajador_detail.html

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-2529.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `centrodeinfancia/templates/centrodeinfancia/trabajador_detail.html`
- `centrodeinfancia/views.py`
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
