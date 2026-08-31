# Contexto de feature PR #2322 - Recupero Pass

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/2322
- Base: `development`
- Rama origen: `Pass-2236`
- Autor: `nehuen871`

## Contexto funcional

- Recuperación autoservicio de contraseña desde el login web de SISOC.

## Arquitectura tocada

- Se modifican templates, con posible impacto visual o de composición UI.

## Decisiones y supuestos detectados

- Tipo de cambio declarado: Seguridad / corrección funcional.
- Área principal declarada: Usuarios y autenticación.
- Impacto usuario declarado: El usuario puede recuperar la contraseña sin intervención administrativa y sin afectar otras cuentas que compartan email.
- Riesgos / rollback: Riesgo bajo y acotado al formulario web y a la generación de artefactos de PR. El rollback puede realizarse revirtiendo el commit correspondiente.

## Design system y UI

- El PR toca piezas de UI y conviene revisar consistencia visual con el patrón existente.
- Archivos visuales relevantes: users/templates/user/login.html, users/templates/user/password_reset_done.html

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-2322.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `docs/contexto/features/pr-2322-recupero-pass.md`
- `docs/plans/2026-08-21-pr-2322-review-fixes-design.md`
- `docs/registro/cambios/2026-08-20-reset-password-issue-2236.md`
- `docs/registro/prs/PR-2322.md`
- `scripts/ci/pr_doc_automation.py`
- `tests/test_pr_doc_automation_unit.py`
- `tests/test_users_auth_flows.py`
- `users/forms.py`
- `users/templates/user/login.html`
- `users/templates/user/password_reset_done.html`
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`
- `docs/contexto/features/pr-2322-recupero-pass.md`
- `docs/plans/2026-08-21-pr-2322-review-fixes-design.md`
- `docs/registro/cambios/2026-08-20-reset-password-issue-2236.md`
- `docs/registro/prs/PR-2322.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
