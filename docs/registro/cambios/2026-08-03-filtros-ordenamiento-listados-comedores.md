# Filtros y ordenamiento en listados de comedores

## Alcance

- El listado de Acompañamiento adopta los filtros combinables disponibles en
  Admisiones, incluyendo filtros favoritos.
- Los listados de Admisiones técnicas, Admisiones legales y Acompañamiento
  permiten ordenar por nombre del comedor desde el encabezado de la tabla.
- En el listado general de comedores se elimina el filtro redundante
  `Estado de actividad`.
- `Estado general` pasa a ofrecer `Activo` e `Inactivo` como opciones.
- `Estado de proceso` y `Estado de detalle` mantienen como valor y etiqueta el
  nombre legible del estado, sin exponer identificadores internos.

## Diseño

Los filtros de Acompañamiento usan el motor compartido
`AdvancedFilterEngine` y una configuración propia, porque el queryset parte de
`Comedor` mientras que los listados de Admisiones parten de `Admision`.
Los campos propios de una admisión se evalúan contra la admisión activa de
Acompañamiento más reciente, que es la misma que se muestra en la fila y se
exporta a CSV.

El ordenamiento por nombre se resuelve en el servidor:

- `Admisiones técnicas`, `Admisiones legales` y `Acompañamiento` aplican el
  orden por nombre sobre el queryset completo antes de paginar.
- El encabezado alterna entre orden ascendente y descendente mediante el
  parámetro GET `ordering`.
- Los enlaces de paginación conservan `ordering` junto con los filtros activos.
- Al cambiar el orden se vuelve a la primera página para evitar resultados
  inconsistentes con la posición anterior.

Las columnas configurables `Estado proceso` y `Estado detalle` del listado
general de comedores seleccionan explícitamente el campo descriptivo `estado`
de cada relación. El template muestra esos nombres legibles en lugar de las
claves foráneas.

## Impacto sobre datos

Los cambios son exclusivamente de consulta y presentación:

- no crean, modifican ni eliminan registros;
- no incorporan migraciones ni alteraciones de modelos;
- no cambian las relaciones de estados existentes;
- los filtros favoritos y las preferencias de columnas existentes continúan
  siendo compatibles.

## Validación

- Tests unitarios de configuración de filtros.
- Tests del ordenamiento validado y de la persistencia de parámetros GET.
- Test del queryset que exige nombres legibles para Proceso y Detalle.
- 126 tests focalizados de views y servicios de Comedores, Acompañamiento y
  Admisiones.
- `manage.py check` sin observaciones.
- Formateo Python con Black y templates con djLint.
