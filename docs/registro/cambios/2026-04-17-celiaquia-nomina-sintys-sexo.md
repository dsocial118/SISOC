# Exportación de nómina Sintys con sexo

## Contexto

En `/celiaquia/expedientes/<pk>/`, la acción **Descargar nómina Sintys** generaba un Excel con las columnas `Numero_documento`, `TipoDocumento`, `nombre` y `apellido`.

## Cambio realizado

- Se agregó la columna `sexo` al archivo Excel exportado desde `CruceService.generar_nomina_sintys_excel`.
- Si el sexo estaba persistido como abreviatura (`M` / `F`), la exportación ahora lo normaliza al texto visible del sistema (`Masculino` / `Femenino`).
- Se mantiene sin cambios el criterio actual de selección de personas exportadas:
  - responsables;
  - beneficiarios sin responsable asociado.
- Se extendió el test de regresión de la exportación para validar el nuevo encabezado y el valor textual exportado desde `ciudadano.sexo`.

## Validación

- `pytest celiaquia/tests/test_nomina_sintys_export.py -q`
