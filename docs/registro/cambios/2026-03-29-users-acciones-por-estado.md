# Listado de usuarios: acciones por fila según estado activo

## Contexto
El PR de activación/desactivación de usuarios agregaba ambas acciones al listado como acciones globales, por lo que cada fila mostraba `Activar` y `Desactivar` al mismo tiempo.

## Cambios realizados
- Se dejó de usar una lista global de acciones para el listado de usuarios.
- Se agregaron filas armadas por usuario en `users/services.py`, con acciones dependientes de `is_active`.
- El template `users/templates/user/user_list.html` pasó a renderizar la tabla en modo `custom_cells` y `custom_actions` para respetar esas acciones por fila.
- Se agregaron tests de regresión para el listado por estado y para la reactivación de usuarios.

## Impacto
- Un usuario activo ahora muestra `Editar` y `Desactivar`.
- Un usuario inactivo ahora muestra `Editar` y `Activar`.
- No cambia el contrato de URLs ni los permisos del módulo.
