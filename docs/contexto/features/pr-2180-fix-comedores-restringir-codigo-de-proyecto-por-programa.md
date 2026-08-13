# Contexto de feature PR #2180 - fix(comedores): restringir código de proyecto por programa

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/2180
- Base: `development`
- Rama origen: `codex/issue-2169-codigo-proyecto`
- Autor: `juanikitro`

## Contexto funcional

- No informado explícitamente; inferir desde el título del PR y el diff.

## Arquitectura tocada

- Se modifican templates, con posible impacto visual o de composición UI.
- Existen cambios de persistencia o migraciones que requieren revisión de datos.

## Decisiones y supuestos detectados

- Tipo de cambio declarado: No informado
- Área principal declarada: No informada
- Impacto usuario declarado: No informado
- Riesgos / rollback: No informado

## Design system y UI

- El PR toca piezas de UI y conviene revisar consistencia visual con el patrón existente.
- Archivos visuales relevantes: comedores/templates/comedor/comedor_form.html

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-2180.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `comedores/forms/comedor_form.py`
- `comedores/migrations/0052_issue_2169_codigo_proyecto.py`
- `comedores/templates/comedor/comedor_form.html`
- `comedores/utils.py`
- `docs/registro/cambios/2026-07-29-issue-2169-codigo-proyecto.md`
- `tests/test_comedor_form_unit.py`
- `tests/test_comedores_utils_unit.py`
- `tests/test_issue_2169_codigo_proyecto_migration.py`
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`
- `docs/registro/cambios/2026-07-29-issue-2169-codigo-proyecto.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
