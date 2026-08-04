# Contexto de feature PR #2165 - feat(organizaciones): mostrar programa en comedores asociados

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/2165
- Base: `development`
- Rama origen: `codex/issue-2164-programa-comedores`
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
- Archivos visuales relevantes: organizaciones/templates/organizacion_detail.html

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-2165.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `docs/registro/cambios/2026-07-28-programa-comedores-asociados.md`
- `organizaciones/templates/organizacion_detail.html`
- `organizaciones/tests.py`
- `organizaciones/views.py`
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`
- `docs/registro/cambios/2026-07-28-programa-comedores-asociados.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
