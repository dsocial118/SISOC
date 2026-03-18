# Fix: mantener DNI como string en comparación RENAPER (Celiaquía)

Fecha: 2026-03-19

## Contexto
En la validación RENAPER de expediente detalle, el frontend compara valores con igualdad estricta (`===`).
Cuando `consultar_datos_renaper()` entrega `dni` numérico, se podía generar falso mismatch visual:

- Provincia: `"12345678"`
- RENAPER: `12345678`

## Cambios
- Archivo: `celiaquia/views/validacion_renaper.py`
- Función: `_formatear_datos_renaper()`
- Se prioriza `dni` (luego `documento`, luego `documento_consulta`) y se normaliza siempre a string en `datos_renaper_formateados["documento"]`.

## Cobertura
- Archivo: `tests/test_validacion_renaper_view_unit.py`
- Se actualiza el test `test_formatear_datos_renaper_usa_provincia_api_cuando_no_hay_pk` para validar que `documento` retorna como string (`"12345678"`).

## Impacto esperado
- Evita falsos negativos de comparación en el modal de validación RENAPER cuando el backend recibe DNI numérico desde el servicio compartido.
- Sin cambios de contrato API en campos no relacionados.
