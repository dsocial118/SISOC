# VAT municipios sin paginacion

Se desactivo la paginacion del endpoint `GET /api/vat/municipios/` para alinear su contrato con `provincias` y `localidades`.

## Impacto
- La respuesta ahora es una lista JSON directa.
- Se mantiene el filtro por `provincia_id`.
- Se agregaron tests de regresion para la lista completa y el filtrado.