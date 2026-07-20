# Nuevos totales en expedientes de pago

## Contexto

El issue `#2045` complementa `#2032` y agrega dos columnas al archivo de carga
de expedientes de pago: `Total Prestaciones` y `Gastos Accesorios 6%`.

## Cambios funcionales

- `ExpedientePago` persiste `total_prestaciones` y `gastos_accesorios`.
- La importacion CSV/XLSX reconoce las cabeceras `Total Prestaciones` y
  `Gastos Accesorios 6%`.
- Los campos se parsean como importes decimales, igual que `Total`.
- El formulario de expediente de pago permite ver y editar ambos campos para
  evitar perdida de datos en ediciones posteriores.
- El detalle de expediente de pago muestra los nuevos campos solo en el bloque
  `Informacion del Expediente`, junto a `Total`.

## Reglas principales

- Los nuevos campos son opcionales para mantener compatibilidad con expedientes
  y archivos historicos.
- No se calcula ni valida automaticamente que `Gastos Accesorios 6%` sea
  exactamente el 6% de `Total Prestaciones`; se persiste el valor informado.

## Validacion

- Tests cercanos de `importarexpediente/tests/test_import_flow.py`.
