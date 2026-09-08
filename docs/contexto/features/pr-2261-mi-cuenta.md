# Contexto de feature PR #2261 - Mi cuenta

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/2261
- Base: `development`
- Rama origen: `MiCuenta`
- Autor: `MariaNavarro90`

## Contexto funcional

- Forzar una actualización masiva de datos personales por única vez y dejar una sección permanente de autogestión. Hasta ahora los datos identificatorios de los usuarios solo se editaban desde el ABM, con perfiles incompletos o desactualizados.

## Arquitectura tocada

- Hay cambios en vistas web y puede existir impacto en permisos o renderizado.
- Se modifican templates, con posible impacto visual o de composición UI.
- Existen cambios de persistencia o migraciones que requieren revisión de datos.

## Decisiones y supuestos detectados

- Tipo de cambio declarado: Nuevas Funcionalidades
- Área principal declarada: users
- Impacto usuario declarado: Alto y visible desde el primer login. Todos los usuarios activos verán una pantalla de confirmación bloqueante en su próximo ingreso web y no podrán operar hasta completar DNI, CUIL, nombre, apellido, mail y aceptar la declaración. Los usuarios que solo operan la PWA no la ven: el middleware exime /api/.
- Riesgos / rollback: El riesgo principal es de soporte, no técnico: exigir DNI y CUIL válidos a todo el padrón activo es un gate duro, y un usuario con el CUIL mal cargado no puede seguir usando el sistema hasta corregirlo. Conviene avisar a soporte antes del deploy. Para desactivar el flujo sin revertir código alcanza con quitar users.middleware.ProfileConfirmationMiddleware de MIDDLEWARE, o bajar el flag en masa con Profile.objects.update(needs_profile_confirmation=False). La 0044 es reversible: su RunPython tiene función inversa. Los campos agregados son aditivos y no rompen lecturas previas.

## Design system y UI

- El PR toca piezas de UI y conviene revisar consistencia visual con el patrón existente.
- Archivos visuales relevantes: static/custom/css/poncho_formularios.css, templates/includes/sidebar/opciones.html, users/templates/user/_mi_cuenta_campos.html, users/templates/user/_mi_cuenta_submit_js.html, users/templates/user/confirmar_datos.html, users/templates/user/mi_cuenta.html

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-2261.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `AGENT_REPO_MAP.md`
- `config/settings.py`
- `docs/registro/cambios/2026-08-06-mi-cuenta-confirmacion-datos.md`
- `static/custom/css/poncho_formularios.css`
- `templates/includes/sidebar/opciones.html`
- `tests/test_users_mi_cuenta.py`
- `tests/urls_vat_comision_horarios.py`
- `users/forms.py`
- `users/middleware.py`
- `users/migrations/0044_profile_confirmacion_datos.py`
- `users/migrations/0045_profile_correo_institucional_declaracion.py`
- `users/models.py`
- `users/profile_utils.py`
- `users/templates/user/_mi_cuenta_campos.html`
- `users/templates/user/_mi_cuenta_submit_js.html`
- `users/templates/user/confirmar_datos.html`
- `users/templates/user/mi_cuenta.html`
- `users/urls.py`
- `users/views.py`
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`
- `docs/registro/cambios/2026-08-06-mi-cuenta-confirmacion-datos.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
