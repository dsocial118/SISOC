# Contexto de feature PR #1368 - Codex/main cherrypick juanikitro no vat

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/1368
- Base: `main`
- Rama origen: `codex/main-cherrypick-juanikitro-no-vat`
- Autor: `juanikitro`

## Contexto funcional

- No informado explícitamente; inferir desde el título del PR y el diff.

## Arquitectura tocada

- Existen cambios de persistencia o migraciones que requieren revisión de datos.

## Decisiones y supuestos detectados

- Tipo de cambio declarado: No informado
- Área principal declarada: No informada
- Impacto usuario declarado: No informado
- Riesgos / rollback: No informado

## Design system y UI

- Sin cambios visibles de UI o design system detectados en el diff.

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-1368.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `ciudadanos/models.py`
- `docs/registro/cambios/2026-03-26-fix-busqueda-ciudadano-documento-timeout.md`
- `tests/test_ciudadanos_models_unit.py`
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`
- `docs/registro/cambios/2026-03-26-fix-busqueda-ciudadano-documento-timeout.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
