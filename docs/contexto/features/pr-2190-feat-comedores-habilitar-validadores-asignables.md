# Contexto de feature PR #2190 - feat(comedores): habilitar validadores asignables

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/2190
- Base: `development`
- Rama origen: `codex/issue-2185-permisos-validacion`
- Autor: `juanikitro`

## Contexto funcional

- No informado explícitamente; inferir desde el título del PR y el diff.

## Arquitectura tocada

- El PR toca lógica en `services/`, por lo que impacta reglas de negocio u orquestación.
- Se modifican templates, con posible impacto visual o de composición UI.

## Decisiones y supuestos detectados

- Tipo de cambio declarado: No informado
- Área principal declarada: No informada
- Impacto usuario declarado: No informado
- Riesgos / rollback: No informado

## Design system y UI

- El PR toca piezas de UI y conviene revisar consistencia visual con el patrón existente.
- Archivos visuales relevantes: comedores/templates/comedor/comedor_detail.html

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-2190.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `comedores/services/validacion_service/impl.py`
- `comedores/templates/comedor/comedor_detail.html`
- `comedores/tests.py`
- `comedores/urls.py`
- `comedores/views/comedor.py`
- `core/constants.py`
- `docs/registro/cambios/2026-07-29-permiso-validar-comedores.md`
- `tests/test_comedor_validation_permissions.py`
- `tests/test_create_groups_command.py`
- `users/bootstrap/groups_seed.py`
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`
- `docs/registro/cambios/2026-07-29-permiso-validar-comedores.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
