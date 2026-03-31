# 2026-03-30 - Columna "Tiene nómina" en listado CDI

## Qué cambió

- Se agregó la columna `Tiene nómina` al listado `/centrodeinfancia/listar`.
- El valor mostrado es `Si` cuando el centro tiene al menos un registro en `nominas`.
- El valor mostrado es `No` cuando el centro no tiene registros en nómina.

## Implementación

- La vista `CentroDeInfanciaListView` anota el queryset con un booleano `tiene_nomina` usando `Exists(...)`.
- El template del listado y su partial de filas renderizan la nueva columna dentro del sistema existente de columnas configurables.
- La columna quedó visible por defecto, pero puede ocultarse manualmente desde la configuración de columnas.

## Validación

- Se agregó un test de regresión para verificar que el listado distingue entre centros con y sin nómina.
