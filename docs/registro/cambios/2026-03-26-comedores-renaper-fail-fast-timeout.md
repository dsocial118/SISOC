# 2026-03-26 - Comedores: fail-fast en consulta RENAPER para evitar timeouts encadenados

## Contexto

En producción se observó caída de worker (`SystemExit`) durante la carga de la vista de nómina al consultar RENAPER.
El flujo actual podía encadenar hasta 3 intentos por sexo (`M/F/X`) aun cuando el primer intento fallaba por integración (timeout/login/red), acumulando latencia hasta superar el timeout de Gunicorn.

## Causa raíz

`ComedorService._consultar_renaper_por_dni` reintentaba por sexo sin discriminar tipo de error.
Ese comportamiento era útil para el caso “sin coincidencia”, pero contraproducente para errores de infraestructura, donde repetir no agrega valor inmediato y aumenta el riesgo de timeout del worker.

## Cambios implementados

- `comedores/services/comedor_service/impl.py`
  - Se ajustó `_consultar_renaper_por_dni` para reintentar por sexo **solo** cuando RENAPER devuelve respuesta de negocio “sin coincidencia” (`raw_response` presente).
  - Ante errores de integración (sin `raw_response`) ahora corta temprano (fail-fast) y devuelve el error del primer intento.

- `tests/test_comedor_service_renaper_helpers_unit.py`
  - Se agregó test de regresión que valida que, ante error de integración, no se ejecutan los 3 intentos por sexo.

## Impacto esperado

- Reduce la latencia acumulada en fallas de RENAPER.
- Disminuye probabilidad de `SystemExit` por timeout de worker en rutas que consultan RENAPER desde request web.
- Mantiene el comportamiento de fallback por sexo para el caso de “sin coincidencia”.
