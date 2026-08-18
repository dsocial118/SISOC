# Contexto de feature PR #2312 - feat(centrodeinfancia): habilitar descarga superadmin [HML]

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/2312
- Base: `homologacion`
- Rama origen: `codex/simepi-descarga-nomina-ninos`
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
- Archivos visuales relevantes: centrodeinfancia/templates/centrodeinfancia/centrodeinfancia_list.html, templates/components/search_bar.html

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-2312.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `centrodeinfancia/templates/centrodeinfancia/centrodeinfancia_list.html`
- `centrodeinfancia/tests/test_nomina_ninos_pdf.py`
- `centrodeinfancia/views.py`
- `centrodeinfancia/views_export.py`
- `docs/contexto/features/pr-2308-feat-centrodeinfancia-descargar-nomina-provincial-de-ninos.md`
- `docs/plans/2026-08-18-simepi-superadmin-nomina-provincial-design.md`
- `docs/plans/2026-08-18-simepi-superadmin-nomina-provincial-plan.md`
- `docs/registro/cambios/2026-08-18-simepi-descarga-nomina-ninos.md`
- `docs/registro/prs/PR-2308.md`
- `templates/components/search_bar.html`
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`
- `docs/contexto/features/pr-2308-feat-centrodeinfancia-descargar-nomina-provincial-de-ninos.md`
- `docs/plans/2026-08-18-simepi-superadmin-nomina-provincial-design.md`
- `docs/plans/2026-08-18-simepi-superadmin-nomina-provincial-plan.md`
- `docs/registro/cambios/2026-08-18-simepi-descarga-nomina-ninos.md`
- `docs/registro/prs/PR-2308.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
