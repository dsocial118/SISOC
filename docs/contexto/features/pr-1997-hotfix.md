# Contexto de feature PR #1997 - hotfix

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/1997
- Base: `main`
- Rama origen: `hoyfix`
- Autor: `dsocial118`

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

- Empezar por `docs/registro/prs/PR-1997.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `centrodefamilia/forms.py`
- `centrodefamilia/migrations/0015_alter_centro_referente.py`
- `centrodefamilia/models.py`
- `centrodefamilia/tests/test_centro_form_referente.py`
- `docs/registro/cambios/2026-07-03-cdf-centro-referente-grupo.md`
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`
- `docs/registro/cambios/2026-07-03-cdf-centro-referente-grupo.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
