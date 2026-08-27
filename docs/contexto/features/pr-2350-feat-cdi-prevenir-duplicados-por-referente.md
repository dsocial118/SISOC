# Contexto de feature PR #2350 - feat(cdi): prevenir duplicados por referente

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/2350
- Base: `development`
- Rama origen: `codex/issue-2349-cdi-duplicados`
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
- Archivos visuales relevantes: centrodeinfancia/templates/centrodeinfancia/centrodeinfancia_form.html

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-2350.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `centrodeinfancia/forms.py`
- `centrodeinfancia/management/__init__.py`
- `centrodeinfancia/management/commands/__init__.py`
- `centrodeinfancia/management/commands/relevar_cdi_duplicados.py`
- `centrodeinfancia/templates/centrodeinfancia/centrodeinfancia_form.html`
- `centrodeinfancia/tests/test_centrodeinfancia_form.py`
- `centrodeinfancia/tests/test_relevar_cdi_duplicados_command.py`
- `docs/registro/cambios/2026-08-26-issue-2349-cdi-duplicados.md`
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`
- `docs/registro/cambios/2026-08-26-issue-2349-cdi-duplicados.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
