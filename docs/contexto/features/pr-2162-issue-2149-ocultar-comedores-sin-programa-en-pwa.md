# Contexto de feature PR #2162 - Issue 2149: ocultar comedores sin programa en PWA

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/2162
- Base: `development`
- Rama origen: `fix/issue-2149`
- Autor: `PabloCao1`

## Contexto funcional

- No informado explícitamente; inferir desde el título del PR y el diff.

## Arquitectura tocada

- Hay cambios en capa API/DRF y conviene revisar contratos de request/response.
- Hay cambios en vistas web y puede existir impacto en permisos o renderizado.

## Decisiones y supuestos detectados

- Tipo de cambio declarado: No informado
- Área principal declarada: No informada
- Impacto usuario declarado: No informado
- Riesgos / rollback: No informado

## Design system y UI

- Sin cambios visibles de UI o design system detectados en el diff.

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-2162.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `comedores/api_views.py`
- `docs/registro/cambios/2026-07-28-issue-2149-visibilidad-pwa-programa.md`
- `tests/test_pwa_colaboradores_api.py`
- `tests/test_pwa_comedores_api.py`
- `tests/test_pwa_formacion_api.py`
- `tests/test_pwa_mensajes_api.py`
- `tests/test_pwa_nomina_api.py`
- `tests/test_pwa_push_api.py`
- `users/services_pwa.py`
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`
- `docs/registro/cambios/2026-07-28-issue-2149-visibilidad-pwa-programa.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
