# Importacion masiva de ciudadanos por CUIL/DNI

## Contexto

Se agrega una seccion en Historia Social Digital para crear lotes de importacion
masiva de ciudadanos desde un archivo `.xlsx` con CUIL o DNI. RENAPER no acepta
CUIL como parametro, por lo que el importador normaliza CUIL a DNI y valida el
digito verificador antes de consultar.

## Decision

- El permiso existente `ciudadanos.add_ciudadano` gobierna descarga de plantilla,
  carga, historial, detalle y reanudacion.
- El upload solo crea un `CiudadanosImportJob`; no procesa filas dentro de la
  request web.
- El worker `process_ciudadanos_import_jobs` procesa fila por fila, con pausa
  configurable entre consultas RENAPER.
- El historial es global para usuarios con permiso, siguiendo el patron de
  credenciales masivas.

## Reglas principales

- La plantilla oficial contiene `cuil_o_dni` y `sexo`; se aceptan aliases reales
  `cuil`, `dni` y `documento`.
- Se aceptan CUILs con separadores (`20-44535030-4`, `20.44535030.4`,
  `20 44535030 4`) y sin separadores (`20445350304`), ademas de DNI directo.
- Si el CUIL es invalido, la fila falla y el lote continua.
- Si `sexo` viene vacio, se consulta RENAPER con `M`, `F` y `X`, en ese orden.
- Si RENAPER devuelve un CUIL distinto al informado en la planilla, la fila falla
  y el lote continua.
- Si ya existe un ciudadano `ESTANDAR` para el DNI, se registra como `existing`
  con link al detalle y no se actualiza.
- Si RENAPER devuelve datos validos y no existe ciudadano `ESTANDAR`, se crea
  con `origen_dato="renaper"`, `estado_validacion_renaper=VALIDADO` y
  `datos_renaper`.
- Errores sistemicos de RENAPER (`timeout`, `auth_error`, `remote_error`,
  `invalid_response`, `unexpected_error`) pausan el lote en `failed` y permiten
  reanudar sin consumir filas pendientes.

## Configuracion

- `DJANGO_SERVICE_ROLE=ciudadanos_import_worker`
- `CIUDADANOS_IMPORT_JOB_POLL_SECONDS`, default `5`
- `CIUDADANOS_IMPORT_JOB_STALE_SECONDS`, default `900`
- `CIUDADANOS_IMPORT_RENAPER_SLEEP_SECONDS`, default `1`
