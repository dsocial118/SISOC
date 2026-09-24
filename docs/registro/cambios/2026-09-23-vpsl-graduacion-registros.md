# VPSL: graduación por ojo en registros nominales

## Contexto

El diagnóstico genérico del registro nominal no representaba la graduación
indicada por el profesional. Además, la matrícula estimada del itinerario dejó
de formar parte de la información operativa visible.

## Cambios

- Se retiró la matrícula estimada de la creación y del detalle del itinerario.
  La columna histórica se conserva para no destruir datos existentes.
- El selector de diagnóstico/prescripción se retiró del formulario activo.
- El registro nominal incorpora `graduacion_izquierda` y
  `graduacion_derecha`, con valores entre `-6` y `+6` e intervalos de `0.25`.
- Ambas graduaciones son obligatorias cuando el resultado es entrega en el
  día, derivación o envío a laboratorio.
- Cuando el resultado es `No requiere anteojos`, las graduaciones se limpian.
- La exportación de jornada reemplaza Prescripción por las dos columnas de
  graduación.

## Integridad y compatibilidad

- El rango y los intervalos se validan en servidor, además de los controles
  numéricos del navegador.
- La antigua columna `prescripcion` se conserva para mantener los datos
  históricos, aunque ya no se edita ni exporta desde el flujo activo.
- La migración consolidada `0015_vpsl_ubicacion_vehiculos_graduaciones` agrega
  columnas anulables, por lo que los registros existentes siguen siendo
  válidos.
