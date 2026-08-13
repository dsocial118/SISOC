# Contexto de feature PR #2283 - fix(comedores): generar certificaciones sin fuente

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/2283
- Base: `development`
- Rama origen: `codex/fix-prestaciones-pdf-fallback`
- Autor: `juanikitro`

## Contexto funcional

- No informado explícitamente; inferir desde el título del PR y el diff.

## Arquitectura tocada

- El PR toca lógica en `services/`, por lo que impacta reglas de negocio u orquestación.
- Hay cambios en capa API/DRF y conviene revisar contratos de request/response.
- Hay cambios en vistas web y puede existir impacto en permisos o renderizado.

## Decisiones y supuestos detectados

- Tipo de cambio declarado: No informado
- Área principal declarada: No informada
- Impacto usuario declarado: No informado
- Riesgos / rollback: No informado

## Design system y UI

- Sin cambios visibles de UI o design system detectados en el diff.

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-2283.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `comedores/api_views.py`
- `comedores/services/certificacion_prestaciones_service.py`
- `docs/contexto/features/pr-2283-fix-comedores-generar-certificaciones-sin-fuente.md`
- `docs/plans/2026-08-13-certificacion-prestaciones-fallback-design.md`
- `docs/registro/cambios/2026-08-13-certificaciones-prestaciones-sin-fuente.md`
- `docs/registro/prs/PR-2283.md`
- `tests/test_certificacion_prestaciones_service_unit.py`
- `tests/test_pwa_comedores_api.py`
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`
- `docs/contexto/features/pr-2283-fix-comedores-generar-certificaciones-sin-fuente.md`
- `docs/plans/2026-08-13-certificacion-prestaciones-fallback-design.md`
- `docs/registro/cambios/2026-08-13-certificaciones-prestaciones-sin-fuente.md`
- `docs/registro/prs/PR-2283.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
