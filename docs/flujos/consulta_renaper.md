# Flujo: Consulta a RENAPER para datos de ciudadanos

## Objetivo
Obtener datos de ciudadanos desde RENAPER mediante una integración compartida,
con cache de token y una fachada compatible para los dominios consumidores.

## Entrada / Salida
- Entrada: DNI y sexo solicitados al servicio RENAPER. Evidencia: `core/integrations/renaper.py`.
- Salida: diccionario compatible con datos de RENAPER mapeados (`nombre`, `apellido`, `cuil`, ubicación API, etc.) o un error clasificado. Evidencia: `core/services/renaper.py`.

## Pasos
1. `APIClient.get_token()` obtiene token desde cache (`renaper_token`) o hace login a `/auth/login` con `RENAPER_API_USERNAME/PASSWORD`.
2. `APIClient.consultar_ciudadano()` llama a `/consultarenaper` con `dni` y `sexo`, usando token en header Authorization.
3. `core.services.renaper.consultar_datos_renaper()` mantiene el contrato compatible y mapea los campos compartidos.
4. La integración clasifica timeout, errores remotos, autenticación, respuesta inválida y falta de coincidencia; la fachada conserva el caso funcional de persona fallecida.

## Validaciones y reglas
- Token cacheado por 50 minutos por defecto; timeout y TTL se configuran con `RENAPER_REQUEST_TIMEOUT_SECONDS` y `RENAPER_TOKEN_CACHE_TTL_SECONDS`.
- Si `mensaf` indica “FALLECIDO”, retorna error.
- Normaliza enteros evitando “0” o vacío.

## Side effects
- Cache de token en `cache.set("renaper_token", ...)`.
- Logs estructurados de operación, tipo de error y status HTTP, sin DNI, token, payload remoto ni credenciales.

## Errores comunes y debug
- Login fallido: revisar credenciales `RENAPER_API_USERNAME/PASSWORD`, conectividad y el evento `renaper.integration.failure`.
- Error decodificar JSON o sin coincidencia: revisar el tipo de error del resultado; los payloads remotos no se exponen ni se registran.
- Datos incompletos: revisar la respuesta funcional del consumidor con datos sintéticos en un entorno de prueba.

## Tests existentes
- `tests/test_consulta_renaper_unit.py` cubre el cliente mockeado, cache, timeout, fallas remotas y normalización.
