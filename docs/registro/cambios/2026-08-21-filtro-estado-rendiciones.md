# Filtro por estado visible en rendiciones mensuales

El filtro `Estado` del listado global ahora usa la combinación de etapa y
subestado que construye el texto mostrado en la columna homónima. Antes filtraba
el campo general histórico `estado`, por lo que la opción elegida podía no
coincidir con las filas visibles esperadas.

El filtro anterior se conserva como `Estado general` para mantener disponibles
los cuatro estados globales y no invalidar filtros favoritos existentes.

Se agregó una prueba de regresión que diferencia rendiciones con el mismo estado
general y subestado, pero pertenecientes a etapas distintas.

El filtro `Etapa` también se alineó con la columna: ahora incluye las cinco
etapas del modelo, incorporando `Carga de documentación` y `Regularización`, que
antes no estaban disponibles.

Como prevención, los catálogos de `Etapa`, `Estado general` y `Línea
programática` dejaron de duplicarse en la configuración de filtros y ahora se
obtienen directamente de las opciones del modelo. La revisión del resto del
panel confirmó que sus lookups coinciden con los campos que presenta el listado.

La edición de datos generales ahora exige inicio y fin del período. Los campos
son anulables en el modelo para soportar registros históricos, pero el formulario
ya no permite enviar fechas vacías y evita el `AttributeError` que se producía al
intentar derivar mes y año desde un valor nulo.
