# Flujo: Consulta a RENAPER para datos de ciudadanos

## Objetivo
Obtener datos de ciudadanos desde RENAPER mediante una integración compartida y
una fachada compatible para los dominios consumidores.

## Entrada / Salida
- Entrada: DNI y sexo solicitados al servicio RENAPER. Evidencia: `core/integrations/renaper.py`.
- Salida: diccionario compatible con datos de RENAPER mapeados (`nombre`, `apellido`, `cuil`, ubicación API, etc.) o un error clasificado. Evidencia: `core/services/renaper.py`.

## Pasos
1. `APIClient.get_token()` hace login a `/auth/login` con `RENAPER_API_USERNAME/PASSWORD` y mantiene el token sólo durante la consulta actual.
2. `APIClient.consultar_ciudadano()` llama a `/consultarenaper` con `dni` y `sexo`, usando token en header Authorization.
3. `core.services.renaper.consultar_datos_renaper()` mantiene el contrato compatible y mapea los campos compartidos.
4. La integración clasifica timeout, errores remotos, autenticación, respuesta inválida y falta de coincidencia; la fachada conserva el caso funcional de persona fallecida.

## Validaciones y reglas
- El timeout se configura con `RENAPER_REQUEST_TIMEOUT_SECONDS` y debe ser positivo; los tokens no se persisten en cache local.
- Si `mensaf` indica “FALLECIDO”, retorna error.
- Normaliza enteros evitando “0” o vacío.

## Side effects
- Logs estructurados de operación, tipo de error y status HTTP, sin DNI, token, payload remoto ni credenciales.

## Errores comunes y debug
- Login fallido: revisar credenciales `RENAPER_API_USERNAME/PASSWORD`, conectividad y el evento `renaper.integration.failure`.
- Error decodificar JSON o sin coincidencia: revisar el tipo de error del resultado; los payloads remotos no se exponen ni se registran en errores o logs. La respuesta exitosa conserva `datos_api` por compatibilidad de la fachada.
- Datos incompletos: revisar la respuesta funcional del consumidor con datos sintéticos en un entorno de prueba.

## Tests existentes
- `tests/test_consulta_renaper_unit.py` cubre el cliente mockeado, cache, timeout, fallas remotas y normalización.
