# Flujo: Consulta a RENAPER para datos de ciudadanos

## Objetivo
Obtener datos de ciudadanos desde RENAPER con cache de token y mapping de campos para usos en centro de familia/ciudadanos.

## Entrada / Salida
- Entrada: DNI y sexo solicitados al servicio RENAPER. Evidencia: centrodefamilia/services/consulta_renaper.py:13-70.
- Salida: diccionario con datos de RENAPER mapeados (`nombre`, `apellido`, `cuil`, ubicación API, etc.) o error. Evidencia: centrodefamilia/services/consulta_renaper.py:107-172.

## Pasos
1. `APIClient.get_token()` obtiene token desde cache (`renaper_token`) o hace login a `/auth/login` con `RENAPER_API_USERNAME/PASSWORD`. Evidencia: centrodefamilia/services/consulta_renaper.py:24-51.
2. `consultar_ciudadano` llama a `/consultarenaper` con `dni` y `sexo`, usando token en header Authorization. Evidencia: centrodefamilia/services/consulta_renaper.py:53-93.
3. `consultar_datos_renaper` envuelve la llamada, valida respuesta y mapea campos a formato interno (incluye `cuil`, `dni`, nombres, ubicación API, etc.). Evidencia: centrodefamilia/services/consulta_renaper.py:107-172.
4. Maneja valores especiales (fallecido, códigos en cero) y normaliza ints con `safe_int`. Evidencia: centrodefamilia/services/consulta_renaper.py:119-171.

## Validaciones y reglas
- Token cacheado por 50 minutos; falla si login no responde. Evidencia: centrodefamilia/services/consulta_renaper.py:24-51.
- Si `mensaf` indica “FALLECIDO”, retorna error. Evidencia: centrodefamilia/services/consulta_renaper.py:119-123.
- Normaliza enteros evitando “0” o vacío. Evidencia: centrodefamilia/services/consulta_renaper.py:134-143.

## Side effects
- Cache de token en `cache.set("renaper_token", ..., 3000)`. Evidencia: centrodefamilia/services/consulta_renaper.py:24-51.
- Logs de errores en login/consulta/JSON. Evidencia: centrodefamilia/services/consulta_renaper.py:40-92.

## Errores comunes y debug
- Login fallido: revisar credenciales `RENAPER_API_USERNAME/PASSWORD` y conectividad; ver logs “Error en login RENAPER”. Evidencia: centrodefamilia/services/consulta_renaper.py:40-44.
- Error decodificar JSON o sin coincidencia: revisar logs “Error decodificar JSON” o “No se encontró coincidencia”. Evidencia: centrodefamilia/services/consulta_renaper.py:69-90.
- Datos incompletos (cuil/ubicación): revisar `raw_response` devuelto en error. Evidencia: centrodefamilia/services/consulta_renaper.py:114-117.

## Tests existentes
- No se encontraron tests para este servicio. Evidencia: DESCONOCIDO (no hay tests/centrodefamilia).***
