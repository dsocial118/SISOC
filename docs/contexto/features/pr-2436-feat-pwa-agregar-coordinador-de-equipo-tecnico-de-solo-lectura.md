# Contexto de feature PR #2436 - feat(pwa): agregar coordinador de equipo técnico de solo lectura

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/2436
- Base: `development`
- Rama origen: `codex/issue-2316-coordinador-pwa`
- Autor: `juanikitro`

## Contexto funcional

- No informado explícitamente; inferir desde el título del PR y el diff.

## Arquitectura tocada

- El PR toca lógica en `services/`, por lo que impacta reglas de negocio u orquestación.
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
- Archivos visuales relevantes: users/templates/user/user_form.html

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-2436.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `AGENT_REPO_MAP.md`
- `comedores/api_views.py`
- `docs/registro/cambios/2026-09-03-usuario-coordinador-pwa.md`
- `pwa/api_views.py`
- `pwa/services/mensajes_service.py`
- `tests/test_pwa_comedores_api.py`
- `tests/test_pwa_mensajes_api.py`
- `tests/test_users_api_permissions_unit.py`
- `tests/test_users_pwa_forms.py`
- `tests/test_users_services_pwa.py`
- `users/api_permissions.py`
- `users/api_views.py`
- `users/forms.py`
- `users/migrations/0049_coordinadorequipotecnico_pwa.py`
- `users/models.py`
- `users/services_pwa.py`
- `users/templates/user/user_form.html`
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`
- `docs/registro/cambios/2026-09-03-usuario-coordinador-pwa.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
