# Relevamientos en legajo para Abordaje Comunitario

## Contexto

Issue #1935 reporto que los comedores con programa `Abordaje Comunitario - Linea Secos` y `Abordaje Comunitario - Linea Tradicional` habian perdido el acceso superior a `Relevamientos` en el legajo, porque el boton fue reemplazado por `Actividades`.

## Cambio

- Se agrega una regla explicita para mostrar el boton `Relevamientos` en el header del legajo solo para esos dos programas de Abordaje Comunitario.
- Para el resto de los comedores PNUD se conserva el comportamiento previo: se muestra `Actividades` sin restaurar `Relevamientos`.
- Para comedores no PNUD se conserva el comportamiento previo: se muestra `Relevamientos`.

## Implementacion

- `comedores.utils.is_abordaje_comunitario_relevamientos_header_program` centraliza la deteccion por nombre normalizado del programa.
- `ComedorDetailView` expone `mostrar_relevamientos_header` al template.
- `comedores/templates/comedor/comedor_detail.html` usa ese flag para renderizar el boton.

## Validacion

- Tests focalizados de helper y render del legajo para:
  - Abordaje Comunitario - Linea Secos con `Actividades` y `Relevamientos`.
  - PNUD fuera de esas dos lineas manteniendo oculto `Relevamientos`.
  - Comedor no PNUD manteniendo `Relevamientos`.
- `black --check` sobre Python tocado.

