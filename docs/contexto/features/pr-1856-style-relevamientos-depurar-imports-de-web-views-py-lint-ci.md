# Contexto de feature PR #1856 - style(relevamientos): depurar imports de web_views.py (lint CI)

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/1856
- Base: `development`
- Rama origen: `claude/stoic-elion-096b9c`
- Autor: `juanikitro`

## Contexto funcional

- Relevamientos — vistas web

## Arquitectura tocada

- Hay cambios en vistas web y puede existir impacto en permisos o renderizado.

## Decisiones y supuestos detectados

- Tipo de cambio declarado: chore / limpieza de imports (lint)
- Área principal declarada: relevamientos
- Impacto usuario declarado: Ninguno (sin cambios funcionales).
- Riesgos / rollback: Riesgo mínimo; revertir el commit restaura el bloque previo. No hay migraciones ni cambios de datos.

## Design system y UI

- Sin cambios visibles de UI o design system detectados en el diff.

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-1856.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `CHANGELOG.md`
- `docs/contexto/features/pr-1856-style-relevamientos-depurar-imports-de-web-views-py-lint-ci.md`
- `docs/registro/prs/PR-1856.md`
- `docs/registro/releases/pending/2026-06-10-pr-1856.md`
- `relevamientos/views/web_views.py`
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`
- `docs/contexto/features/pr-1856-style-relevamientos-depurar-imports-de-web-views-py-lint-ci.md`
- `docs/registro/prs/PR-1856.md`
- `docs/registro/releases/pending/2026-06-10-pr-1856.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
