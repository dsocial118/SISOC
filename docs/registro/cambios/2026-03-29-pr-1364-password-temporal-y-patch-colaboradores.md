# Ajustes de seguridad y regresiones en PR 1364

## Qué cambió

- Se eliminó la persistencia en base de datos de la contraseña temporal visible para usuarios mobile.
- La contraseña generada automáticamente sigue siendo la contraseña real del usuario, pero su visualización quedó limitada a la sesión del admin que crea el usuario.
- Se corrigió la edición de usuarios legacy sin `Profile` en vistas, middleware y serialización de contexto.
- Se corrigió el `PATCH` de colaboradores PWA para que no borre actividades cuando `actividad_ids` no forma parte del payload.

## Motivo

- Evitar guardar credenciales en texto plano sin perder la visibilidad operativa requerida al momento de crear usuarios mobile.
- Cubrir una regresión de actualización parcial en colaboradores.
- Evitar errores `Profile.DoesNotExist` en usuarios históricos.

## Validación esperada

- La UI de edición sigue mostrando la contraseña temporal inmediatamente después de crear el usuario mobile.
- El usuario creado puede iniciar sesión con esa contraseña mientras no la cambie.
- Un `PATCH` parcial de colaborador conserva las actividades existentes si no se envía `actividad_ids`.
- Abrir la edición de un usuario sin `Profile` ya no produce error.
