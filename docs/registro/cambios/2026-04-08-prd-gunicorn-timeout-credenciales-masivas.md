# 2026-04-08 - Produccion: timeout de Gunicorn alineado para credenciales masivas

## Contexto

El flujo de `/usuarios/credenciales-masivas/` usa `GUNICORN_TIMEOUT` para
calcular su presupuesto total de procesamiento. Si ese valor no esta definido,
el service cae al default de 30 segundos y corta el lote bastante antes.

Ademas, Gunicorn real no estaba recibiendo un `--timeout` explicitamente desde
la configuracion productiva versionada en el repo.

## Cambio aplicado

- Se agrego `GUNICORN_TIMEOUT=300` a `.env.prod`.
- Se agrego `GUNICORN_CMD_ARGS="--timeout 300"` a `.env.prod`.

Con esto:

- el lote de credenciales calcula un presupuesto de 295 segundos;
- Gunicorn queda alineado para esperar hasta 300 segundos por request;
- el mensaje de corte preventivo solo aparece cuando el lote realmente se
  acerca al maximo de 5 minutos del request web.

## Validacion

- Revision manual de `.env.prod`.
- Verificacion de coherencia contra `users/services_bulk_credentials.py` y
  `docker/django/entrypoint.py`.

## Limite conocido

Esto aumenta la ventana maxima de procesamiento, pero no vuelve asincrono el
flujo. Un Excel lo suficientemente grande o un SMTP muy lento todavia pueden
consumir esos 5 minutos.
