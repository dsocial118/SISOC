# Contexto de feature PR #2228 - fix(iam): restringe accesos de ciudadanos y acompanamiento

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/2228
- Base: `development`
- Rama origen: `codex/issue-2225-grupos-permisos`
- Autor: `juanikitro`

## Contexto funcional

- No informado explícitamente; inferir desde el título del PR y el diff.

## Arquitectura tocada

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
- Archivos visuales relevantes: comedores/templates/comedor/nomina_detail.html

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-2228.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `acompanamientos/urls.py`
- `acompanamientos/views.py`
- `ciudadanos/urls.py`
- `ciudadanos/views.py`
- `ciudadanos/views_export.py`
- `comedores/templates/comedor/nomina_detail.html`
- `docs/registro/cambios/2026-08-04-issue-2225-permisos-grupos.md`
- `tests/test_acompanamientos_views_unit.py`
- `tests/test_ciudadanos_views_unit.py`
- `tests/test_issue_2225_permissions.py`
- `users/bootstrap/groups_seed.py`
- `users/migrations/0042_revoke_acompanamiento_from_comedores_groups.py`
- `users/migrations/0043_merge_issue_2225_profile_datos_identificatorios.py`
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`
- `docs/registro/cambios/2026-08-04-issue-2225-permisos-grupos.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
