# Contexto de feature PR #2279 - feat(admisiones): corregir expedientes del issue 2272

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/2279
- Base: `development`
- Rama origen: `codex/issue-2272-expedientes`
- Autor: `juanikitro`

## Contexto funcional

- No informado explícitamente; inferir desde el título del PR y el diff.

## Arquitectura tocada

- No se detectó un patrón arquitectónico dominante más allá del diff observado.

## Decisiones y supuestos detectados

- Tipo de cambio declarado: No informado
- Área principal declarada: No informada
- Impacto usuario declarado: No informado
- Riesgos / rollback: No informado

## Design system y UI

- Sin cambios visibles de UI o design system detectados en el diff.

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-2279.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `AGENT_REPO_MAP.md`
- `admisiones/data/issue_2272_expedientes.csv`
- `admisiones/management/__init__.py`
- `admisiones/management/commands/__init__.py`
- `admisiones/management/commands/corregir_expedientes_issue_2272.py`
- `admisiones/tests/test_corregir_expedientes_issue_2272.py`
- `docs/indice.md`
- `docs/operacion/comandos_administracion.md`
- `docs/operacion/correccion_expedientes_issue_2272.md`
- `docs/registro/cambios/2026-08-12-issue-2272-correccion-expedientes.md`
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`
- `docs/operacion/comandos_administracion.md`
- `docs/operacion/correccion_expedientes_issue_2272.md`
- `docs/registro/cambios/2026-08-12-issue-2272-correccion-expedientes.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
