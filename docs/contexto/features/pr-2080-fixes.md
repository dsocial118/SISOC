# Contexto de feature PR #2080 - fixes

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/2080
- Base: `development`
- Rama origen: `CUIT-Legajo-Organizacion-1865`
- Autor: `nehuen871`

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
- Archivos visuales relevantes: organizaciones/templates/organizacion_form.html

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-2080.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `docs/registro/cambios/2026-07-16-validacion-cuit-organizaciones.md`
- `organizaciones/forms.py`
- `organizaciones/templates/organizacion_form.html`
- `organizaciones/tests.py`
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`
- `docs/registro/cambios/2026-07-16-validacion-cuit-organizaciones.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
