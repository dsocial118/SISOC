# Contexto de feature PR #2231 - style(templates): corrige formato para promocion a homologacion

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/2231
- Base: `development`
- Rama origen: `codex/fix-pr-2229-djlint`
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
- Archivos visuales relevantes: admisiones/templates/admisiones/admisiones_tecnicos_form.html, templates/includes/base.html, templates/includes/sidebar/new_opciones.html

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-2231.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `admisiones/templates/admisiones/admisiones_tecnicos_form.html`
- `templates/includes/base.html`
- `templates/includes/sidebar/new_opciones.html`
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
