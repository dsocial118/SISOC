# Contexto de feature PR #1925 - fix(comedores): alinear monto_prestacion_mensual mobile con la web

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/1925
- Base: `main`
- Rama origen: `claude/fix-monto-prestacion-mobile-aprobadas`
- Autor: `juanikitro`

## Contexto funcional

- No informado explícitamente; inferir desde el título del PR y el diff.

## Arquitectura tocada

- El PR toca lógica en `services/`, por lo que impacta reglas de negocio u orquestación.
- Hay cambios en capa API/DRF y conviene revisar contratos de request/response.

## Decisiones y supuestos detectados

- Tipo de cambio declarado: No informado
- Área principal declarada: No informada
- Impacto usuario declarado: No informado
- Riesgos / rollback: No informado

## Design system y UI

- Sin cambios visibles de UI o design system detectados en el diff.

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-1925.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `comedores/api_serializers.py`
- `comedores/services/comedor_service/impl.py`
- `tests/test_comedor_service_renaper_helpers_unit.py`
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
