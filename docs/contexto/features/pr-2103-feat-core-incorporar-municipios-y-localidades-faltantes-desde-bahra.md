# Contexto de feature PR #2103 - feat(core): incorporar municipios y localidades faltantes desde BAHRA

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/2103
- Base: `development`
- Rama origen: `claude/sisoc-bhara-instances-2d3319`
- Autor: `juanikitro`

## Contexto funcional

- No informado explícitamente; inferir desde el título del PR y el diff.

## Arquitectura tocada

- El PR toca lógica en `services/`, por lo que impacta reglas de negocio u orquestación.

## Decisiones y supuestos detectados

- Tipo de cambio declarado: No informado
- Área principal declarada: No informada
- Impacto usuario declarado: No informado
- Riesgos / rollback: No informado

## Design system y UI

- Sin cambios visibles de UI o design system detectados en el diff.

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-2103.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `core/fixtures/localidad_municipio_provincia.json`
- `core/management/commands/load_fixtures.py`
- `core/services/territorio_sync.py`
- `docs/registro/cambios/2026-07-17-bajada-bahra-territorio.md`
- `scripts/actualizar_territorio_desde_bahra.py`
- `tests/test_actualizar_territorio_desde_bahra.py`
- `tests/test_load_fixtures_command.py`
- `tests/test_territorio_sync.py`
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`
- `docs/registro/cambios/2026-07-17-bajada-bahra-territorio.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
