# Contexto de feature PR #2547 - fix(users): usar el template de activación en UserActiveView (#2520)

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/2547
- Base: `development`
- Rama origen: `Fix-mensaje-#2520`
- Autor: `nehuen871`

## Contexto funcional

- Gestión de usuarios (alta/baja lógica desde /usuarios/).

## Arquitectura tocada

- Hay cambios en vistas web y puede existir impacto en permisos o renderizado.
- Se modifican templates, con posible impacto visual o de composición UI.

## Decisiones y supuestos detectados

- Tipo de cambio declarado: bugfix
- Área principal declarada: users
- Impacto usuario declarado: Admins con permiso auth.delete_user. Solo cambia el texto y el color del botón de la pantalla de confirmación; la acción y los permisos no cambian.
- Riesgos / rollback: Riesgo bajo, sin cambios de datos, permisos ni contratos. Rollback = revertir el commit; confirm_class es retrocompatible por default.

## Design system y UI

- El PR toca piezas de UI y conviene revisar consistencia visual con el patrón existente.
- Archivos visuales relevantes: templates/components/delete_confirm.html, users/templates/user/user_confirm_active.html

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-2547.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `docs/contexto/features/pr-2547-fix.md`
- `docs/registro/prs/PR-2547.md`
- `templates/components/delete_confirm.html`
- `tests/test_users_auth_flows.py`
- `users/templates/user/user_confirm_active.html`
- `users/views.py`
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
