# Contexto de feature PR #2553 - fix(datacalle): la fase no habilitaba área operativa ni el desplegable de dispositivos

## Resumen

- PR: https://github.com/secretarianaf/SISOC/pull/2553
- Base: `main`
- Rama origen: `fix/datacalle-toggle-fase`
- Autor: `Mkdir-arg`

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
- Archivos visuales relevantes: datacalle/templates/datacalle/relevamiento_form.html

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-2553.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `datacalle/templates/datacalle/relevamiento_form.html`
- `docs/registro/cambios/2026-09-17-datacalle-qa-segundo-bloque.md`
- `tests/test_datacalle_relevamientos.py`
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
