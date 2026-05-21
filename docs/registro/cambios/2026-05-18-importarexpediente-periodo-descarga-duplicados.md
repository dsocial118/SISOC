# Importacion de expedientes: periodo, descarga y duplicados

## Contexto

El flujo de importacion de expedientes de pago incorpora controles y datos
visibles sobre el archivo importado. El lote conserva el expediente de pago
detectado, el periodo de pago y el archivo original para consulta posterior por
el usuario que hizo la carga.

## Cambios funcionales

- `ArchivosImportados` guarda `mes_pago` y `ano_pago` del archivo importado.
- El listado de importaciones muestra el periodo normalizado como `MM/YYYY`.
- Los lotes historicos sin periodo persistido completan el dato desde registros
  importados o desde el archivo almacenado cuando se consulta el listado.
- El listado permite descargar el archivo importado original.
- El upload rechaza archivos cuyo expediente de pago ya exista en otro lote
  importado o en `ExpedientePago`.
- Los errores de archivo vacio o sin cabecera vuelven al formulario de carga y
  muestran el mensaje al usuario, sin crear un lote fallido.

## Reglas principales

- El periodo se arma con `Mes de Pago` y `Ano de pago`.
- Los meses aceptan numeros (`1`, `01`) y nombres en castellano.
- El anio se normaliza a cuatro digitos cuando el valor importado trae formato
  numerico de planilla.
- La descarga del archivo importado queda limitada al usuario propietario del
  lote.
- El control de duplicados compara expediente de pago sin distinguir mayusculas
  y minusculas.

## Validacion

- Tests cercanos de `importarexpediente/tests` cubren periodo persistido,
  backfill de lotes historicos, descarga, duplicados y errores de upload.
- `makemigrations importarexpediente --check --dry-run` no detecta cambios
  pendientes sobre el modelo.
