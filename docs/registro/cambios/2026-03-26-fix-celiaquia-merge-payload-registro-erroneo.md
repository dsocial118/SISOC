# Fix Celiaquía: merge de payload en actualización de registros erróneos

## Fecha
2026-03-26

## Contexto
Se detectó un caso en el que `ActualizarRegistroErroneoView` podía sobrescribir `datos_raw` con un payload parcial y perder campos obligatorios que no venían en la solicitud (por ejemplo `sexo`), lo que luego generaba errores al reprocesar.

## Cambios aplicados
- Se agregó consolidación de datos en backend (`datos_raw` previo + campos recibidos) antes de validar y guardar en `ActualizarRegistroErroneoView`.
- Se mantiene el comportamiento de limpieza para campos enviados vacíos (`""`), que siguen removiéndose y validándose como faltantes.
- Se agregó cobertura de tests:
  - Unit test para verificar que una actualización parcial conserva `sexo` y actualiza solo el campo enviado.
  - Test de integración para validar el merge de campos omitidos en la actualización de `RegistroErroneo`.

## Impacto
- Evita pérdida involuntaria de campos obligatorios en guardados parciales.
- Reduce errores de reproceso causados por sobrescritura incompleta de `datos_raw`.
- No cambia contratos públicos de endpoints ni reglas de validación existentes.
