# Cambio VAT: selector de plan curricular sin filtro por modalidad

## Fecha

- 2026-04-11

## Alcance

- Se eliminó del front el filtro `Modalidad` del modal `Seleccionar Plan Curricular` en la sección de cursos del detalle de centros VAT.
- Se mantuvo visible la columna `Modalidad` dentro de la tabla del listado para conservar el contexto del usuario al elegir un plan.

## Decisión de implementación

- El cambio se resolvió solo en el front del modal, retirando el control visual y la lógica JavaScript asociada al filtrado por modalidad.
- Se conservaron los filtros restantes: búsqueda general y sector.

## Validación esperada

- Al abrir `Nuevo Curso` en `.../vat/centros/<id>/#cursos`, el modal de selección de plan curricular muestra únicamente los filtros `Buscar` y `Sector`.
- La tabla sigue mostrando la columna `Modalidad`.
