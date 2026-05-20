# Celiaquia: nomina de aprobados en Excel

## Contexto

El detalle de expediente de Celiaquia ya exponia la URL `padron-final`, pero el
archivo generado no respetaba la estructura de la nomina provincial original y
el acceso aparecia antes de finalizar el cruce SINTYS.

## Cambio

- La descarga `expedientes/<id>/padron-final/` conserva la URL publica y ahora
  genera `nomina_aprobados_<expediente_id>.xlsx`.
- El Excel se recalcula desde `Expediente.excel_masivo`, usando la primera hoja
  como fuente de encabezados, orden de columnas y datos originales.
- Solo se exportan filas cuyo documento pertenece a un legajo del expediente con
  revision tecnica aprobada y resultado SINTYS `MATCH`.
- Los responsables no se agregan como filas propias: si sus datos existen en la
  fila original del beneficiario, quedan preservados en esas columnas.
- El boton del detalle se muestra solo con cruce finalizado, Excel original
  disponible y usuario autorizado.

## Validacion

- Tests focalizados del servicio y vista de descarga.
- Tests del detalle de expediente.
- Chequeos de formato sobre Python y template afectado.
