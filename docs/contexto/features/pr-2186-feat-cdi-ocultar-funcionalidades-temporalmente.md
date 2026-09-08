# Contexto de feature PR #2186 - feat(cdi): ocultar funcionalidades temporalmente

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/2186
- Base: `development`
- Rama origen: `codex/issue-2182-cdi-ocultar`
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
- Archivos visuales relevantes: centrodeinfancia/templates/centrodeinfancia/centrodeinfancia_detail.html

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-2186.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `.env.example`
- `centrodeinfancia/templates/centrodeinfancia/centrodeinfancia_detail.html`
- `centrodeinfancia/tests/test_cdi_feature_visibility.py`
- `centrodeinfancia/tests/test_formulario_cdi_views.py`
- `centrodeinfancia/views.py`
- `config/settings.py`
- `docs/registro/cambios/2026-07-29-issue-2182-cdi-ocultamiento-temporal.md`
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`
- `docs/registro/cambios/2026-07-29-issue-2182-cdi-ocultamiento-temporal.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
