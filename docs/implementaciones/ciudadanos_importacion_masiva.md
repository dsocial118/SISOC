# Importacion masiva de ciudadanos

## Objetivo

Permitir que usuarios con permiso de alta de ciudadanos creen lotes de importacion desde planillas con CUIL o DNI, procesados fuera de la request web mediante un worker dedicado.

## Superficies

- UI: Historia Social Digital expone descarga de plantilla, carga de planilla, historial de lotes, detalle y exportacion de resultados.
- Backend web: el upload crea un `CiudadanosImportJob` y no procesa filas en la request.
- Worker: `python manage.py process_ciudadanos_import_jobs` toma lotes pendientes y procesa fila por fila.
- Deploy productivo: `docker-compose.produccion.yml` levanta `ciudadanos_import_worker` con `DJANGO_SERVICE_ROLE=ciudadanos_import_worker`.

## Reglas funcionales

- La plantilla oficial usa `cuil_o_dni` y `sexo`; se aceptan aliases reales `cuil`, `dni` y `documento`.
- CUIL se normaliza a DNI y se valida el digito verificador antes de consultar RENAPER.
- Si `sexo` viene vacio, el worker consulta RENAPER con `M`, `F` y `X`, en ese orden.
- Si RENAPER devuelve un CUIL distinto al informado, la fila falla y el lote continua.
- Si ya existe un ciudadano `ESTANDAR` para el DNI, la fila queda como `existing` y no actualiza datos.
- Si RENAPER devuelve datos validos y no existe ciudadano `ESTANDAR`, se crea el ciudadano con `origen_dato="renaper"`, `estado_validacion_renaper=VALIDADO` y `datos_renaper`.
- Los IDs de catalogos o ubicacion devueltos por el mapeo local se normalizan a campos `_id` antes de crear el ciudadano.
- Errores sistemicos de RENAPER pausan el lote en estado fallido reanudable; errores puntuales de fila no bloquean el resto.

## Configuracion

- `DJANGO_SERVICE_ROLE=ciudadanos_import_worker`
- `CIUDADANOS_IMPORT_JOB_POLL_SECONDS`: default `5`.
- `CIUDADANOS_IMPORT_JOB_STALE_SECONDS`: default `900`.
- `CIUDADANOS_IMPORT_RENAPER_SLEEP_SECONDS`: default `1`.

## Operacion

1. Ejecutar migraciones antes de habilitar la carga.
2. Confirmar que el servicio `ciudadanos_import_worker` esta levantado en produccion.
3. Revisar logs del worker ante lotes sin avance.
4. Para diagnostico puntual, ejecutar `python manage.py process_ciudadanos_import_jobs --once` en un contenedor con las mismas variables.

## Riesgos

- RENAPER puede limitar o demorar consultas; conservar la pausa entre filas evita saturar el servicio externo.
- No correr el worker deja los lotes creados pero pendientes.
- Cambiar `CIUDADANOS_IMPORT_JOB_STALE_SECONDS` demasiado bajo puede duplicar toma de lotes en despliegues con reinicios lentos.
