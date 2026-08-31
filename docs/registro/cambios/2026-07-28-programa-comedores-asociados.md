# Programa en comedores asociados de Organización

## Cambio

El detalle de Organización ahora muestra el programa de cada comedor asociado
en una columna específica. Para los comedores históricos sin programa cargado,
la vista muestra `-`.

## Alcance técnico

La consulta del detalle incorpora la relación `programa` mediante `select_related`
para evitar consultas adicionales por fila. No se modificaron datos, modelos,
migraciones, rutas ni permisos.
