# 2026-04-09 - Worker de credenciales: fallback de logs ante permisos insuficientes

## Contexto

El servicio `bulk_credentials_worker` podia no iniciar aunque la cola de lotes
estuviera correcta. La causa no estaba en el procesamiento de credenciales sino
en la inicializacion global de logging de Django.

En contenedores con el repo montado en `/sisoc`, el handler diario podia
intentar abrir archivos como `/sisoc/logs/YYYY-MM-DD/critical.log` y fallar con
`PermissionError`, lo que abortaba todo el proceso antes de que el worker
ejecutara `manage.py process_bulk_credentials_jobs`.

## Cambio aplicado

- Se robustecio `core.utils.DailyFileHandler`.
- Ahora intenta usar el path diario configurado normalmente.
- Si el archivo o su directorio no son escribibles, cambia automaticamente a
  `LOG_FALLBACK_DIR` en lugar de abortar el arranque del proceso.
- Se imprime un aviso en `stderr` con el path rechazado y el fallback usado.

## Impacto

- El worker de credenciales puede arrancar y consumir lotes aun cuando el
  volumen montado del repo no permita escribir en `/sisoc/logs`.
- El comportamiento se aplica tambien al resto de procesos Django que usen el
  mismo handler, sin cambiar el contrato de logging existente.

## Validacion prevista

- `pytest core/tests/test_utils_logging.py -q`

## Supuesto

Se asume que `LOG_FALLBACK_DIR` apunta a una ruta escribible del contenedor.
Por defecto, el proyecto ya documenta `/tmp/sisoc-logs`.
