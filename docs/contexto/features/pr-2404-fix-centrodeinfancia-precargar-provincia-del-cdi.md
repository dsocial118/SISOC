# Contexto de feature PR #2404 - fix(centrodeinfancia): precargar provincia del CDI

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/2404
- Base: `development`
- Rama origen: `codex/cdi-default-provincia`
- Autor: `juanikitro`

## Contexto funcional

- No informado explícitamente; inferir desde el título del PR y el diff.

## Arquitectura tocada

- Hay cambios en vistas web y puede existir impacto en permisos o renderizado.

## Decisiones y supuestos detectados

- Tipo de cambio declarado: No informado
- Área principal declarada: No informada
- Impacto usuario declarado: No informado
- Riesgos / rollback: No informado

## Design system y UI

- Sin cambios visibles de UI o design system detectados en el diff.

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-2404.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `centrodeinfancia/tests/test_destinatario_views.py`
- `centrodeinfancia/tests/test_trabajadores_views.py`
- `centrodeinfancia/views.py`
- `docs/plans/2026-08-31-cdi-provincia-inicial-design.md`
- `docs/registro/cambios/2026-08-31-cdi-precarga-provincia-altas.md`
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`
- `docs/plans/2026-08-31-cdi-provincia-inicial-design.md`
- `docs/registro/cambios/2026-08-31-cdi-precarga-provincia-altas.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
