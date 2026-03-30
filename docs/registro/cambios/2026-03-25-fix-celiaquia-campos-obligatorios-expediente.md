# 2026-03-25 - Fix campos obligatorios en importacion de expedientes de Celiaquia

## Que se corrigio
- La importacion de expedientes ahora trata como obligatorios todos los campos del legajo, excepto `telefono`, `email`, `telefono_responsable` y `email_responsable`.
- Cuando falta un dato obligatorio, el registro ya no se procesa como valido: se guarda como `RegistroErroneo`, se informa el motivo y queda editable para su correccion y reproceso.
- La pantalla de detalle del expediente ahora muestra tambien los campos obligatorios del responsable dentro del editor de registros erroneos.
- El guardado desde frontend ahora muestra una alerta de validacion cuando faltan campos obligatorios, en lugar de fallar en silencio.

## Causa raiz
- El flujo de importacion solo exigia un subconjunto minimo de campos (`apellido`, `nombre`, `documento`, `fecha_nacimiento`), por lo que datos clave como `sexo` podian omitirse sin bloquear el alta.
- Durante la normalizacion del payload se descartaban algunos valores faltantes o no resueltos sin convertirlos en error de validacion.
- El editor de registros erroneos no exponia todos los campos requeridos del responsable y el JavaScript no mostraba feedback cuando faltaban datos obligatorios.

## Impacto funcional
- Un expediente cargado sin `sexo`, `nacionalidad`, `municipio`, `localidad`, domicilio o datos obligatorios del responsable ya no ingresa al procesamiento normal.
- Los registros observados pueden corregirse desde la UI y reprocesarse sin perder el detalle del error.
- La plantilla Excel generada por el modulo usa `SEXO_RESPONSABLE` para evitar colisiones con la columna `SEXO` del beneficiario.

## Validacion
- Se agregaron tests de regresion para:
  - importacion con `sexo` faltante,
  - render del editor de registros erroneos con campos del responsable,
  - rechazo de actualizacion cuando faltan campos obligatorios.
- Ejecucion validada:
  - `docker compose run --rm --no-deps -e USE_SQLITE_FOR_TESTS=1 django pytest -n auto celiaquia/tests/test_expediente_plantilla_excel.py celiaquia/tests/test_registros_erroneos_obligatorios.py tests/test_celiaquia_expediente_view_helpers_unit.py tests/test_importacion_service_helpers_unit.py -k "obligatorios or plantilla or actualizar_registro_erroneo_view_paths or payload_row_and_defaults_validation"`
  - Resultado: `8 passed`.
