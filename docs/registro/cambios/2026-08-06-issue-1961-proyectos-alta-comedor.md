# Issue 1961: proyectos disponibles al crear un comedor

## Problema

Un usuario autorizado a crear comedores podÃ­a abrir el formulario, pero la consulta
AJAX de proyectos exigÃ­a permisos adicionales de Organizaciones. Por eso el selector
quedaba vacÃ­o en el primer intento y reciÃ©n se reconstruÃ­a luego de un POST invÃ¡lido.

AdemÃ¡s, el resumen del legajo de OrganizaciÃ³n mezclaba proyectos activos con cÃ³digos
histÃ³ricos de comedores, mientras que el selector solo admite proyectos activos.

## Cambio

- El endpoint de proyectos admite los permisos para crear o editar comedores, sin
  quitar el filtrado de organizaciones accesibles para el usuario.
- El resumen de la OrganizaciÃ³n muestra como proyectos disponibles la misma fuente
  usada por el selector: `ProyectoOrganizacion` activos.
- El formulario informa una falla de carga y sincroniza Select2 al completar opciones.
- Los cambios de OrganizaciÃ³n y Programa se escuchan mediante jQuery, el mismo canal
  de eventos utilizado por Select2.

## ValidaciÃ³n

Se agregÃ³ una regresiÃ³n que verifica el acceso con `comedores.add_comedor` y que el
endpoint devuelve solamente los proyectos activos de la organizaciÃ³n.
