# Contexto de feature PR #2454 - fix(users): preservar permisos al suspender acceso mobile

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/2454
- Base: `development`
- Rama origen: `codex/issue-2316-mobile-access`
- Autor: `juanikitro`

## Contexto funcional

- No informado explícitamente; inferir desde el título del PR y el diff.

## Arquitectura tocada

- Se modifican templates, con posible impacto visual o de composición UI.
- Existen cambios de persistencia o migraciones que requieren revisión de datos.

## Decisiones y supuestos detectados

- Tipo de cambio declarado: No informado
- Área principal declarada: No informada
- Impacto usuario declarado: No informado
- Riesgos / rollback: No informado

## Design system y UI

- El PR toca piezas de UI y conviene revisar consistencia visual con el patrón existente.
- Archivos visuales relevantes: static/custom/js/user_mobile_access.js, tests/js/user_mobile_access.test.js, users/templates/user/user_form.html

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-2454.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `AGENT_REPO_MAP.md`
- `docs/registro/cambios/2026-09-07-2316-acceso-mobile-y-selecciones.md`
- `static/custom/js/user_mobile_access.js`
- `tests/js/user_mobile_access.test.js`
- `tests/test_users_pwa_forms.py`
- `users/forms.py`
- `users/migrations/0050_profile_configuracion_mobile.py`
- `users/models.py`
- `users/templates/user/user_form.html`
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`
- `docs/registro/cambios/2026-09-07-2316-acceso-mobile-y-selecciones.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
