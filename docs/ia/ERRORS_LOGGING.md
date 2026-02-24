# ERRORS_LOGGING.md

Guía para manejo de errores, excepciones y logging en cambios asistidos por IA.

Fuente de verdad general: `../../AGENTS.md`.

## Alineación con el repo (importante)

El proyecto ya tiene configuración de logging en `config/settings.py` y utilidades en `core/utils.py`:
- handlers por nivel (`info`, `warning`, `error`, `critical`)
- handler de datos estructurados (`data_file`)
- `core.utils.DailyFileHandler`
- `core.utils.JSONDataFormatter`

No introducir un esquema paralelo sin necesidad.

## Estrategia de errores (por capa)

## Views / Endpoints

- Validar inputs y devolver status codes coherentes.
- Responder mensajes claros al usuario/cliente (en español).
- No exponer stack traces o detalles internos.

## Services

- Manejar errores esperables (validación/reglas) explícitamente.
- Para fallas inesperadas: log + propagar o traducir según contrato del servicio.
- Mantener side effects consistentes (rollback/transacción cuando corresponda).

## Integraciones externas

- Capturar fallas de red/parsing/timeout.
- Loggear contexto mínimo útil.
- Devolver fallback o error controlado según el flujo.

## Cuándo usar excepciones vs resultados de validación

Usar validación (respuesta controlada / form / serializer) cuando:
- input del usuario es inválido,
- falta parámetro,
- regla de negocio rechaza la operación de forma esperable.

Usar excepción cuando:
- ocurre una falla inesperada,
- falla una integración,
- se rompe una precondición interna,
- hay error de infraestructura.

## Status codes: mapeo práctico

- `400`: input inválido / request mal formado.
- `401`: no autenticado (si aplica al flujo).
- `403`: autenticado sin permisos.
- `404`: recurso no encontrado.
- `409`: conflicto de negocio/estado (si aplica).
- `500`: error inesperado.

Usar el código más específico que represente el problema real.

## Mensajes: usuario vs técnico

## Mensajes al usuario / respuesta API

- En español.
- Claros, cortos y accionables.
- Sin detalles internos (SQL, traces, tokens, paths internos, credenciales).

Ejemplo bueno:
- `{"error": "Parámetro page inválido."}`

## Mensajes técnicos (logs)

- Incluir contexto suficiente para debug.
- Evitar PII/secretos.
- Usar `logger.exception(...)` para conservar traceback cuando se captura una excepción.

## Logging: reglas de uso

## Logger por defecto

Usar por defecto:

```python
import logging

logger = logging.getLogger(__name__)
```

Solo usar nombres específicos de logger si hay un motivo operativo claro.

## Niveles (uso sugerido)

- `debug`: detalle de diagnóstico (solo si aporta).
- `info`: eventos normales relevantes.
- `warning`: situación inesperada recuperable / fallback aplicado.
- `error`: fallo que afecta la operación actual.
- `exception`: igual que error pero con traceback (dentro de `except`).
- `critical`: fallas graves de sistema.

## Placeholders y contexto

Preferir placeholders en logs para evitar overhead y mantener consistencia:

```python
logger.warning("No se encontró imagen original: %s", image_path)
```

También se puede usar contexto estructurado cuando aporta (alineado al formatter JSON):

```python
logger.info(
    "Evento de negocio",
    extra={"data": {"comedor_id": comedor_id, "accion": "actualizacion"}},
)
```

## Qué NO loggear

- contraseñas,
- tokens/API keys,
- documentos/emails/teléfonos completos,
- payloads completos con PII,
- secretos de entorno.

## Patrones recomendados de manejo de errores

## 1) Capturar, loggear, re-lanzar (si el caller decide)

```python
try:
    procesar()
except Exception:
    logger.exception("Error procesando admisión")
    raise
```

## 2) Capturar, loggear y fallback controlado

```python
try:
    data = cargar_desde_integracion()
except Exception:
    logger.exception("Falló integración externa; usando fallback")
    data = []
```

## 3) Validación con respuesta explícita (sin excepción inesperada)

```python
if not listado:
    return JsonResponse({"error": "Listado inválido."}, status=400)
```

## Integraciones externas: fallback y observabilidad

Cuando un flujo depende de terceros:
- registrar el fallo con contexto mínimo,
- aplicar fallback si existe,
- no ocultar errores silenciosamente,
- cubrir con tests el camino de error cuando sea importante.

## Checklist de errores/logs (rápido)

- Elegí status code correcto.
- Mensaje al usuario en español y sin detalles internos.
- Log técnico útil con contexto mínimo.
- Usé `logger.exception` si capturé excepción.
- No logueé secretos/PII.
- Cubrí caso de error/fallback con test si aplica.

## Ejemplos concretos

## Ejemplo A - `logger.exception` en service

```python
try:
    generar_documento()
except Exception:
    logger.exception("Error generando documento para admisión %s", admision_id)
    raise
```

## Ejemplo B - respuesta de validación en view

```python
if columnas is None:
    return JsonResponse({"error": "Columnas inválidas."}, status=400)
```
