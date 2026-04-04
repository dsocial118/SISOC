# Mobile nómina: baja lógica desde detalle de persona

Fecha: 2026-03-30

## Resumen

Se agregó en SISOC Mobile la acción de baja lógica de una persona de nómina desde la pantalla de detalle individual.

## Cambios

- Se incorporó un botón largo rojo al final del detalle de persona con el texto `Dar de baja de la nómina`.
- Antes de ejecutar la acción, la app solicita confirmación al usuario.
- La acción reutiliza el endpoint existente de baja lógica de nómina.
- Al completarse la baja, la navegación vuelve al listado de nómina del espacio activo.
- Se eliminó la acción `Editar datos` del detalle porque Mobile no permite modificar los datos personales.
- La acción `Sumar a actividad` se movió dentro de la card de actividades de la persona.

## Alcance

- No se modificó la API backend.
- No se agregó borrado físico; la baja sigue el comportamiento lógico ya existente del sistema.

## Validación esperada

- La persona puede darse de baja desde su detalle.
- La acción requiere confirmación explícita.
- Si la baja se completa, la persona deja de aparecer en el listado activo de nómina.
