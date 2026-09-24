# Flujo: Consulta a RENAPER para datos de ciudadanos

## Objetivo
Obtener datos de ciudadanos desde RENAPER mediante una integración compartida y
una fachada compatible para los dominios consumidores.

## Entrada / Salida
- Entrada: DNI y sexo solicitados al servicio RENAPER. Evidencia: `core/integrations/renaper.py`.
- Salida: diccionario compatible con datos de RENAPER mapeados (`nombre`, `apellido`, `cuil`, ubicación API, etc.) o un error clasificado. Evidencia: `core/services/renaper.py`.

## Pasos
1. `APIClient.get_token()` hace login a `/auth/login` con `RENAPER_API_USERNAME/PASSWORD`. Las consultas comunes usan un token efímero por llamada; la importación masiva de ciudadanos reutiliza un cliente y su token sólo en memoria durante el lote. Ante 401 renueva el token una vez.
2. `APIClient.consultar_ciudadano()` llama a `/consultarenaper` con `dni` y `sexo`, usando token en header Authorization.
3. `core.services.renaper.consultar_datos_renaper()` mantiene el contrato compatible y mapea los campos compartidos.
4. La integración clasifica timeout, errores remotos, autenticación, respuesta inválida y falta de coincidencia; la fachada conserva el caso funcional de persona fallecida.

## Validaciones y reglas
- El timeout se configura con `RENAPER_REQUEST_TIMEOUT_SECONDS` y debe ser positivo; los tokens no se persisten en cache local.
- Cada llamada a `/consultarenaper`, incluido un reintento tras 401, reserva un turno en `core.integrations.renaper_rate_limit` mediante una fila bloqueada en MySQL. El límite global configurable `RENAPER_MAX_CONSULTAS_POR_SEGUNDO` inicia en 30, bajo el cupo aproximado informado de 35 consultas/s. Los logins no se cuentan. Requiere la migración `core.0009` antes de atender consultas.
- Si la reserva falla por base de datos, no se envía la consulta; el resultado técnico se clasifica como `rate_limit_unavailable`. Una falla de base al mapear los catálogos se clasifica como `database_unavailable`; el importador trata ambos casos como sistémicos y deja la fila pendiente.
- Si `mensaf` indica “FALLECIDO”, retorna error.
- Normaliza enteros evitando “0” o vacío.

## Side effects
- Logs estructurados de operación, tipo de error y status HTTP, sin DNI, token, payload remoto ni credenciales.

## Errores comunes y debug
- Login fallido: revisar credenciales `RENAPER_API_USERNAME/PASSWORD`, conectividad y el evento `renaper.integration.failure`.
- Error decodificar JSON o sin coincidencia: revisar el tipo de error del resultado; los payloads remotos no se exponen ni se registran en errores o logs. La respuesta exitosa conserva `datos_api` por compatibilidad de la fachada.
- Datos incompletos: revisar la respuesta funcional del consumidor con datos sintéticos en un entorno de prueba.

## Tests existentes
- `tests/test_consulta_renaper_unit.py` cubre el cliente mockeado, autenticación efímera sin cache, timeout, fallas remotas y normalización.
