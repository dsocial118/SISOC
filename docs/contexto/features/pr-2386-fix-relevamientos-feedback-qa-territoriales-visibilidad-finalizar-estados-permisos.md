# Contexto de feature PR #2386 - fix(relevamientos): feedback QA territoriales (visibilidad, finalizar, estados, permisos)

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/2386
- Base: `main`
- Rama origen: `fix/territorial-feedback-qa`
- Autor: `Mkdir-arg`

## Contexto funcional

- No informado explícitamente; inferir desde el título del PR y el diff.

## Arquitectura tocada

- Hay cambios en capa API/DRF y conviene revisar contratos de request/response.
- Hay cambios en vistas web y puede existir impacto en permisos o renderizado.
- Se modifican templates, con posible impacto visual o de composición UI.
- Existen cambios de persistencia o migraciones que requieren revisión de datos.

## Decisiones y supuestos detectados

- Tipo de cambio declarado: No informado
- Área principal declarada: No informada
- Impacto usuario declarado: No informado
- Riesgos / rollback: No informado

## Design system y UI

- El PR toca piezas de UI y conviene revisar consistencia visual con el patrón existente.
- Archivos visuales relevantes: relevamientos/templates/relevamiento_detail.html

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-2386.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `comedores/api_views_territorial.py`
- `relevamientos/migrations/0013_alter_relevamiento_options.py`
- `relevamientos/models.py`
- `relevamientos/service.py`
- `relevamientos/templates/relevamiento_detail.html`
- `relevamientos/views/api_views.py`
- `tests/test_create_groups_command.py`
- `tests/test_relevamiento_api_patch.py`
- `tests/test_relevamientos_service_unit.py`
- `tests/test_territorial_api.py`
- `users/bootstrap/groups_seed.py`
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
