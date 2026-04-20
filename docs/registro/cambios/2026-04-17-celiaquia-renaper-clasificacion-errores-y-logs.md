# Celiaquia: clasificacion de errores, retries y logs de validacion RENAPER

Fecha: 2026-04-17

## Contexto
El endpoint `celiaquia/expedientes/{pk}/legajos/{legajo_id}/validar-renaper` estaba mezclando errores transitorios de RENAPER con errores funcionales de datos del ciudadano.

Eso generaba tres problemas principales:

- mensajes funcionales incorrectos o demasiado genericos para el usuario,
- retries sobre casos no reintentables como `no_match`,
- logs ruidosos o duplicados, donde un mismo caso podia verse como `response_error` y tambien como error funcional.

El objetivo del cambio fue separar explicitamente:

- errores tecnicos o transitorios del servicio externo,
- respuestas invalidas del proveedor,
- errores funcionales de coincidencia de datos del ciudadano.

## Decision principal
Se consolidó un contrato de clasificacion por `error_type` en el servicio compartido de RENAPER y la vista de Celiaquia pasó a decidir retries, mensaje funcional y tipo de log a partir de esa clasificacion.

Los tipos usados quedan:

- `timeout`
- `remote_error`
- `auth_error`
- `invalid_response`
- `unexpected_error`
- `no_match`
- `fallecido`

## Cambios realizados

### 1. Servicio RENAPER
Archivo: `centrodefamilia/services/consulta_renaper/impl.py`

- Se agregó `RenaperServiceError` para clasificar fallas de login/autenticacion/integracion.
- `consultar_ciudadano()` ahora devuelve resultados con `error_type` explicito para:
  - timeout,
  - auth error,
  - remote error,
  - invalid response,
  - no match.
- `consultar_datos_renaper()` propaga la clasificacion y agrega:
  - `fallecido`,
  - `unexpected_error`,
  - `raw_response` cuando aporta contexto util.
- Se restauraron comentarios previos validos del archivo.
- No se incorporaron cambios de SSL local, `verify`, CA bundle, variables nuevas de entorno ni workarounds de certificados.

### 2. Vista de validacion RENAPER
Archivo: `celiaquia/views/validacion_renaper.py`

- Se agregaron mensajes funcionales diferenciados:
  - indisponibilidad remota/transitoria:
    `No pudimos validar con RENAPER en este momento. Por favor, intentá nuevamente en unos minutos.`
  - respuesta invalida:
    `RENAPER devolvió una respuesta inválida y no pudimos completar la validación. Intentá nuevamente más tarde.`
  - no coincidencia:
    `RENAPER no pudo validar los datos ingresados. Verificá el DNI y el sexo registrados.`
- La logica de retry quedó limitada a errores transitorios o tecnicos:
  - `timeout`
  - `remote_error`
  - `auth_error`
  - `invalid_response`
  - `unexpected_error`
- `no_match` deja de reintentarse.
- `no_match` deja de disparar `renaper.validation.retrying_remote_query`.
- Se consolidó el detalle util del log final de error con:
  - `stage`
  - `error`
  - `error_type`
  - `retry_attempt`
  - `max_retries`
  - `raw_response_excerpt`
  - mas el contexto existente del legajo/ciudadano/usuario

### 3. Logging operativo
Archivo: `celiaquia/views/validacion_renaper.py`

Se normalizaron los eventos:

- `renaper.validation.no_match`
  - severidad: `info`
  - no duplica `renaper.validation.response_error`
- `renaper.validation.remote_unavailable`
  - severidad: `warning`
  - para `timeout`, `remote_error`
- `renaper.validation.remote_unavailable` con `auth_error`
  - severidad: `error`
- `renaper.validation.invalid_response`
  - severidad: `error`
- `renaper.validation.fallecido`
  - severidad: `info`
- `renaper.validation.response_error`
  - queda solo para errores genericos o no clasificados especificamente

## Archivos tocados
- `celiaquia/views/validacion_renaper.py`
- `centrodefamilia/services/consulta_renaper/impl.py`
- `tests/test_validacion_renaper_view_unit.py`
- `tests/test_consulta_renaper_unit.py`

## Cobertura agregada o actualizada

### Vista
Archivo: `tests/test_validacion_renaper_view_unit.py`

Se cubren estos casos:

- `no_match` no reintenta
- `no_match` no genera `retrying_remote_query`
- `no_match` no duplica `response_error`
- timeout reintenta y respeta backoff
- error transitorio muestra mensaje funcional correcto
- invalid response muestra mensaje funcional correcto
- flujo exitoso sigue funcionando
- `fallecido` sigue funcionando

### Servicio
Archivo: `tests/test_consulta_renaper_unit.py`

Se cubren estos casos:

- `no_match`
- `timeout`
- `auth_error`
- `invalid_response`
- propagacion de `remote_error`
- clasificacion de `fallecido`
- payload invalido del ciudadano

## Validacion ejecutada

### Pytest dentro del ambiente Docker de la app
Comando:

```bash
docker compose run --rm django pytest tests/test_validacion_renaper_view_unit.py tests/test_consulta_renaper_unit.py
```

Resultado:

```text
25 passed in 2.44s
```

### Validacion de sintaxis
Comando:

```bash
python -m py_compile \
  BACKOFFICE/centrodefamilia/services/consulta_renaper/impl.py \
  BACKOFFICE/celiaquia/views/validacion_renaper.py \
  BACKOFFICE/tests/test_validacion_renaper_view_unit.py \
  BACKOFFICE/tests/test_consulta_renaper_unit.py
```

Resultado: OK

## Impacto esperado
- El usuario recibe mensajes mas precisos y accionables segun el problema real.
- Los retries dejan de ocurrir sobre errores funcionales del ciudadano.
- Los logs quedan mas legibles para operacion y soporte.
- `no_match` deja de verse como error tecnico del sistema.
- Se preserva el comportamiento exitoso y el caso `fallecido`.
