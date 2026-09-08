# Contexto de feature PR #2088 - fix(users): credenciales PWA y descarga CSV por lote

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/2088
- Base: `development`
- Rama origen: `codex/issue-2086`
- Autor: `juanikitro`

## Contexto funcional

- No informado explícitamente; inferir desde el título del PR y el diff.

## Arquitectura tocada

- Se modifican templates, con posible impacto visual o de composición UI.

## Decisiones y supuestos detectados

- Tipo de cambio declarado: No informado
- Área principal declarada: No informada
- Impacto usuario declarado: No informado
- Riesgos / rollback: No informado

## Design system y UI

- El PR toca piezas de UI y conviene revisar consistencia visual con el patrón existente.
- Archivos visuales relevantes: users/templates/user/user_import_job_detail.html

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-2088.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `AGENT_REPO_MAP.md`
- `docs/registro/cambios/2026-07-17-importacion-usuarios-pwa-csv-credenciales.md`
- `tests/test_users_import_export.py`
- `users/services_user_import.py`
- `users/templates/user/user_import_job_detail.html`
- `users/urls.py`
- `users/views_user_import.py`
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`
- `docs/registro/cambios/2026-07-17-importacion-usuarios-pwa-csv-credenciales.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
