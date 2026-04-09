# 2026-04-08 - Credenciales masivas: lotes persistidos, worker dedicado y reanudacion

## Contexto

El envio masivo de credenciales corria dentro de la request web
`/usuarios/credenciales-masivas/`. Con archivos grandes o con un SMTP lento,
el proceso podia morir por timeout de Gunicorn en distintas etapas
(`check_password`, `SMTP AUTH`, `SMTP DATA`), dejando `500` y sin un estado
operativo claro para continuar.

Ademas, el operador necesitaba dos cosas que el flujo sincrono no podia
garantizar de forma robusta:

- saber siempre la causa del error;
- saber hasta que usuario se habia enviado correctamente para poder continuar.

## Cambio aplicado

- Se reemplazo el procesamiento sincrono por un flujo de **lote persistido**:
  - al subir el Excel, la web solo valida formato y crea un `BulkCredentialsJob`;
  - el archivo queda guardado y el detalle del lote muestra estado, error,
    ultimo usuario exitoso y ultimo usuario intentado.
- Se agrego un modelo `BulkCredentialsJobRow` para persistir el resultado por
  fila ya procesada.
- El lote se procesa fuera de la request web mediante un worker dedicado basado
  en Django (`manage.py process_bulk_credentials_jobs`) y un servicio
  `users/services_bulk_credentials_jobs.py`.
- El procesamiento ahora **se detiene en la primera falla**. La fila fallida
  queda registrada y el lote pasa a `failed`.
- Se agrego accion de **Reanudar**:
  - reencola el mismo archivo ya subido;
  - retoma desde la fila fallida (`next_row_index`);
  - conserva el historial previo y vuelve a intentar la fila pendiente.
- Se agrego deteccion de lotes `processing` que queden colgados por caida del
  worker. Si pasan el umbral de inactividad, se marcan como `failed` con un
  mensaje reanudable.
- Se agrego un servicio dedicado en `docker-compose.yml` y `docker/django/entrypoint.py`
  para correr el worker fuera del proceso web:
  - `bulk_credentials_worker`
  - `DJANGO_SERVICE_ROLE=bulk_credentials_worker`

## UX y operacion

- La pantalla de carga ahora crea un lote y redirige al detalle en lugar de
  mostrar el resultado inline.
- El detalle del lote muestra:
  - estado del lote;
  - filas procesadas/enviadas/rechazadas;
  - ultimo usuario enviado correctamente;
  - ultimo usuario intentado;
  - causa del error;
  - tabla paginada de filas procesadas;
  - boton `Reanudar` cuando el lote falla.
- La pantalla principal lista los ultimos lotes del operador actual para evitar
  mezclar ejecuciones de distintos usuarios.

## Validacion

Se agregaron o actualizaron tests para:

- creacion del lote y persistencia del archivo;
- corte en la primera falla con checkpoint y ultimo usuario exitoso;
- reanudacion desde la fila fallida;
- marcado de lotes stale;
- vistas de alta, detalle y reanudacion;
- comando de management del worker;
- dispatch del entrypoint segun `DJANGO_SERVICE_ROLE`.

Comandos previstos de validacion:

- `pytest tests/test_users_bulk_credentials.py tests/test_docker_entrypoint_unit.py -q`
- `black --check users/services_bulk_credentials.py users/services_bulk_credentials_jobs.py users/views.py tests/test_users_bulk_credentials.py tests/test_docker_entrypoint_unit.py docker/django/entrypoint.py`
- `djlint users/templates/user/bulk_credentials_form.html users/templates/user/bulk_credentials_job_detail.html --check --configuration=.djlintrc`

En este host puntual no fue posible ejecutarlos end-to-end porque:

- no hay `python/pytest` disponible en PATH;
- Docker Desktop no estaba levantado, por lo que tampoco se pudo correr la
  suite en contenedor.

## Supuesto

Se asume que el despliegue del worker dedicado se realiza junto con el cambio
de la web. Si el worker no esta corriendo, los lotes quedan en `pending` y no
avanzan, aunque la UI siga mostrando el estado correctamente.
