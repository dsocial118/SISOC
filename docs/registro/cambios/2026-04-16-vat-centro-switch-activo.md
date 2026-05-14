# VAT centros: conservar estado activo al editar

## Contexto

En `/vat/centros/` la edición de un centro podía dejarlo inactivo aunque el usuario solo cambiara datos descriptivos como dirección o correo. Además, una sede inactiva no podía volver a activarse desde el formulario.

## Cambio aplicado

- Se agregó un switch `Activo` al final del formulario de edición de centros.
- La edición ahora conserva el valor actual de `activo` cuando el formulario no expone ni envía el switch.
- La edición permite desactivar o reactivar el centro cuando el usuario opera explícitamente el switch.

## Decisión clave

Se distinguió entre:

- formularios viejos o parciales que no envían el campo `activo`, donde se preserva el estado persistido;
- formularios nuevos que sí envían el marcador `activo_present`, donde el backend respeta el valor elegido por el usuario.

## Validación esperada

- Editar un centro activo sin tocar el switch no debe cambiar su estado.
- Editar un centro activo con el switch apagado debe dejarlo inactivo.
- Editar un centro inactivo con el switch encendido debe reactivarlo.
