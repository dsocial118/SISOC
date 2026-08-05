# Contexto de feature PR #2156 - fix(sidebar): mover expedientes de pago a comedores

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/2156
- Base: `development`
- Rama origen: `codex/issue-2153-mover-expedientes-pago`
- Autor: `juanikitro`

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
- Archivos visuales relevantes: templates/includes/sidebar/opciones.html

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-2156.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `core/tests/test_sidebar_menu.py`
- `docs/registro/cambios/2026-07-27-issue-2153-mover-expedientes-pago.md`
- `templates/includes/sidebar/opciones.html`
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`
- `docs/registro/cambios/2026-07-27-issue-2153-mover-expedientes-pago.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
