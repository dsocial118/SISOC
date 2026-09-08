# Contexto de feature PR #2398 - fix(cdi): habilitar gestión de referentes para SIMEPI EGP

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/2398
- Base: `development`
- Rama origen: `codex/fix-simepi-egp-referentes-cdi`
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

- Empezar por `docs/registro/prs/PR-2398.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `centrodeinfancia/access.py`
- `centrodeinfancia/templates/centrodeinfancia/centrodeinfancia_detail.html`
- `centrodeinfancia/tests/test_access_scope_centrodeinfancia.py`
- `centrodeinfancia/tests/test_generar_usuario_cdi.py`
- `centrodeinfancia/views.py`
- `docs/plans/2026-08-31-simepi-egp-referentes-cdi-design.md`
- `docs/registro/cambios/2026-08-31-simepi-egp-gestiona-referentes-cdi.md`
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`
- `docs/plans/2026-08-31-simepi-egp-referentes-cdi-design.md`
- `docs/registro/cambios/2026-08-31-simepi-egp-gestiona-referentes-cdi.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
