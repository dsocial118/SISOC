# 2026-09-23 — Recuperación y rendimiento de importaciones (#2560, #2561)

Los workers persistentes cierran conexiones antiguas de Django antes y después de cada ciclo para recuperarse de una conexión MySQL perdida sin reiniciar el contenedor.

Los lotes de ciudadanos reutilizan un cliente RENAPER durante su procesamiento; la consulta usa un turno de tasa global y los checkpoints de ciudadano, fila y contadores se guardan de forma transaccional. Las consultas se pueden preparar en paralelo mientras el worker principal persiste los resultados en orden. Los lotes de ciudadanos y usuarios reciben un identificador de propiedad al ser reclamados; si un lote queda inactivo, vuelve a pendiente y un worker anterior no puede confirmar nuevas filas.

Para reducir la carga inicial del servidor, cada réplica prepara hasta dos consultas en paralelo por defecto (cuatro entre ambas réplicas). El lector recorre las celdas del Excel secuencialmente y sólo conserva la lista de filas procesables; deja de mantener simultáneamente una segunda lista completa de celdas. Un `.env` existente puede conservar otro valor de paralelismo y debe revisarse antes de desplegar. El cambio reduce memoria transitoria, pero no demuestra capacidad de CPU/RAM ni el objetivo de siete días sin mediciones.

El Compose de HML/PRD levanta dos réplicas del importador de ciudadanos para que un lote extenso deje disponible otra réplica. El chequeo funcional de PRD verifica ambas. Si quedan otros lotes pendientes, los importadores de ciudadanos y usuarios ceden el turno después de unos treinta minutos de procesamiento por tramo (`CIUDADANOS_IMPORT_JOB_SLICE_SECONDS` y `USER_IMPORT_JOB_SLICE_SECONDS`). Cada tramo vuelve a leer el archivo; hay que medir ese costo en QA con archivos grandes.

El importador de usuarios conserva una sola réplica: dos lotes podrían modificar la misma cuenta y disparar correos de credenciales al mismo tiempo. La cesión de turno acota la espera de otros lotes sin introducir esa carrera.

El envío de credenciales continúa después de completar el lote. Si el proceso cae entre el envío y su registro, `credentials_sent_at` queda vacío y el caso requiere revisión manual antes de reintentar: no se reenvía automáticamente un lote ya completado. El proveedor de correo podría haber aceptado el mensaje y un reintento manual podría duplicarlo.

Antes de desplegar, aplicar las migraciones `core.0009`, `ciudadanos.0033` y `users.0053`. Revisar la variable efectiva `CIUDADANOS_IMPORT_RENAPER_SLEEP_SECONDS`: un `.env` existente con valor `1` conserva la espera anterior; fijarla en `0` para usar el límite global. No modificar credenciales ni tokens durante la migración. En QA, medir una muestra sin sexo, verificar el cupo RENAPER y cortar conexiones MySQL de los workers. El objetivo de 200.000 filas en menos de siete días requiere esa medición y luego observación en producción; este registro no afirma que ya esté demostrado.
