# Importacion de fechas de acreditacion por lote

## Contexto

Se requiere completar `Fecha de Acreditacion` para expedientes de
pago despues de importar y generar un lote de `/importarexpedientes`.

## Cambios funcionales

- La importacion principal reconoce las cabeceras `Fecha de Acreditacion` y
  `Fecha de Acreditación` y las persiste en `ExpedientePago.fecha_acreditacion`
  cuando el archivo original trae el dato.
- El detalle de un lote importado agrega la accion `Actualizar fechas de
  acreditacion` cuando el lote ya esta completado y el usuario tiene permiso de
  cambio.
- El nuevo flujo acepta CSV o XLSX simple con columnas `ID` y `Fecha de
  Acreditacion`.
- Las actualizaciones se aplican solo sobre expedientes asociados al lote actual
  mediante `RegistroImportado`.

## Reglas principales

- El lote debe tener `importacion_completada=True`.
- Si el XLSX o CSV contiene un ID que no pertenece al lote actual, se rechaza toda la
  carga y no se modifica ningun expediente.
- Si un ID aparece repetido con fechas distintas, se rechaza la carga.
- La fecha es obligatoria por fila y debe parsear como fecha valida. El formato
  recomendado para usuarios es `DD/MM/AAAA`, por ejemplo `20/02/2025`.
- El endpoint requiere `importarexpediente.change_archivosimportados` o
  `expedientespagos.change_expedientepago`.

## Validacion

- `pytest importarexpediente/tests -q`
