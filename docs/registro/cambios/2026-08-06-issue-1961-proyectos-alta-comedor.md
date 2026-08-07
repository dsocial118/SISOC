# Issue 1961: proyectos disponibles al crear un comedor

## Problema

Un usuario autorizado a crear comedores podía abrir el formulario, pero la consulta
AJAX de proyectos exigía permisos adicionales de Organizaciones. Por eso el selector
quedaba vacío en el primer intento y recién se reconstruía luego de un POST inválido.

Además, el resumen del legajo de Organización mezclaba proyectos activos con códigos
históricos de comedores, mientras que el selector solo admite proyectos activos.

## Cambio

- El endpoint de proyectos admite los permisos para crear o editar comedores, sin
  quitar el filtrado de organizaciones accesibles para el usuario.
- El resumen de la Organización muestra como proyectos disponibles la misma fuente
  usada por el selector: `ProyectoOrganizacion` activos.
- El formulario informa una falla de carga y sincroniza Select2 al completar opciones.
- Los cambios de Organización y Programa se escuchan mediante jQuery, el mismo canal
  de eventos utilizado por Select2.

## Validación

Se agregó una regresión que verifica el acceso con `comedores.add_comedor` y que el
endpoint devuelve solamente los proyectos activos de la organización.
