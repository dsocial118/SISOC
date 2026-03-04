# SECURITY_AI.md

Reglas de seguridad para cambios asistidos por IA en SISOC.

Fuente de verdad general: `../../AGENTS.md`.

## Objetivo

Reducir errores comunes de seguridad generados por IA (exposición de secretos, permisos débiles, validaciones incompletas, logs con datos sensibles).

## Reglas críticas (obligatorias)

- No hardcodear credenciales, tokens ni secretos.
- No loggear PII, tokens o contraseñas.
- Respetar permisos/autenticación existentes por defecto.
- Validar/sanitizar entradas antes de usar datos del request.
- No abrir endpoints o bypass de seguridad “para simplificar”.

## Secretos y credenciales

- Usar variables de entorno / settings.
- No incluir secretos en tests, ejemplos, docs ni fixtures.
- Si un valor debe existir, documentar nombre de env var, no un secreto real.

Incorrecto:

```python
API_KEY = "123456-secreto-real"
```

Correcto:

```python
api_key = settings.MI_INTEGRACION_API_KEY
```

## PII / datos sensibles

Tratar como sensibles (ejemplos frecuentes):
- documentos,
- emails,
- teléfonos,
- direcciones,
- tokens,
- payloads completos de integraciones.

Reglas:
- no loggear valores completos,
- no copiar datos reales en tests/docs,
- anonimizar ejemplos cuando sea necesario.

## Auth y autorización

- Respetar autenticación configurada (`SessionAuthentication`, `TokenAuthentication`, API key donde aplica).
- Mantener permisos existentes salvo pedido explícito.
- En endpoints nuevos, definir permisos de forma explícita.
- Agregar tests de permisos (sin permiso / con permiso).

Nota del repo:
- existen helpers/permisos API key en `core/api_auth.py` (`HasAPIKey`, `HasAPIKeyOrToken`).

## Validación y sanitización de entrada

- Validar `GET`, `POST`, JSON body y headers relevantes.
- Preferir serializers/forms para validación estructurada cuando aplica.
- Convertir y validar tipos (int, date, bool) antes de operar.
- No asumir que el cliente envía valores válidos.

## Redirects seguros

Si el redirect depende de input del usuario (`next`, referer, etc.):
- usar helper seguro (`core/security.py` -> `safe_redirect`) o patrón equivalente.
- no redirigir directamente a URLs provistas por el usuario sin validar host.

Ejemplo (correcto):

```python
from core.security import safe_redirect

return safe_redirect(request, default="inicio")
```

## SQL / ORM seguro

- Preferir ORM Django.
- No concatenar SQL con inputs del usuario.
- Evitar construir filtros inseguros sin validación.

## Uploads, archivos y rutas

- Validar inputs de paths/rutas antes de abrir archivos.
- No asumir que una ruta recibida es local/segura.
- Limitar side effects de archivos y manejar errores con fallback/logs.

## Config de seguridad por entorno

- No relajar settings de seguridad (`SECURE_*`, CSP, cookies, SSL redirect) sin pedido explícito.
- Si un cambio requiere ajuste de seguridad, documentar impacto y entorno afectado (`dev/qa/prd`).

## Migrations y scripts de datos

- No incluir datos reales en migraciones o scripts.
- Evitar migraciones destructivas sin justificar impacto.
- Si hay data migration, procurar que sea reversible cuando sea viable.

## Integraciones externas

- Manejar errores/timeout de forma segura.
- No exponer detalles internos de infraestructura al usuario final.
- Loggear contexto mínimo útil (sin secretos).

## Checklist de seguridad (rápido)

- No hardcodeé secretos.
- No logueé PII/tokens.
- Validé input del request.
- Respeté permisos/auth existentes.
- Agregué tests de permisos/errores cuando aplica.
- No relajé settings de seguridad sin pedido.

## Ejemplos concretos

## Ejemplo A - anti patrón de logging (incorrecto)

```python
logger.error("Error con token %s para usuario %s", token, email)
```

## Ejemplo A - corrección (mejor)

```python
logger.error("Error de autenticación en integración externa", extra={"data": {"usuario_id": user_id}})
```

## Ejemplo B - validación de parámetro antes de uso

```python
page_raw = request.GET.get("page", "1")
try:
    page = int(page_raw)
except (TypeError, ValueError):
    return JsonResponse({"error": "Parámetro page inválido."}, status=400)
```
