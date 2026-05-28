# 2026-05-27 - Integración SISOC ↔ Ticketera

## Contexto

- La Ticketera (servidor separado, Django + PostgreSQL) necesita autenticar a
  sus usuarios contra las credenciales gestionadas por SISOC, que actúa como
  fuente de verdad. La Ticketera no almacena contraseñas propias.
- Decisión de arquitectura y contratos detallados en
  [docs/registro/decisiones/2026-05-27-integracion-ticketera.md](../decisiones/2026-05-27-integracion-ticketera.md).

## Cambios aplicados

- **App nueva `integracion/`** registrada en `INSTALLED_APPS` y montada en
  `config/urls.py` bajo `/api/integracion/`.
- **Endpoints REST** protegidos por API Key (`core.api_auth.HasAPIKey`),
  canal server-to-server:
  - `POST /api/integracion/ticketera/usuarios/` — alta o reconciliación
    idempotente de usuario. Respuestas: `201` (alta nueva), `200` (ya existía
    con `source=ticketera`), `400` (payload inválido o contraseña débil),
    `409` (username ocupado por otro origen).
  - `POST /api/integracion/ticketera/auth/verificar/` — verificación de
    credenciales. Respuestas: `200` (válidas, informa `must_change_password`),
    `401` (inválidas o usuario inactivo), `429` (rate limit).
- **Modelo:** se agrega `Profile.source` (CharField, `max_length=50`, default
  `"sisoc"`) para distinguir el origen del alta y soportar la lógica
  idempotente. Migración `users/migrations/0031_profile_source.py`.
- **Auditoría:** las operaciones corren dentro de
  `audittrail.context.audit_context(source="integracion:ticketera", ...)`. El
  alta queda registrada vía `auditlog`; en `verificar` se emite un `LogEntry`
  explícito de tipo `ACCESS` porque guardar solo `last_login` no genera diff.
- **Rate limit:** `users.rate_limits.hit_rate_limit` en `verificar` (scope
  `ticketera_verificar`, 10 intentos por username cada 5 minutos).
- **Documentación OpenAPI (`drf-spectacular`):** ambas vistas anotadas con
  `@extend_schema` (tag `Integración Ticketera`, `request` y `responses` por
  status real, incluido `503`). Aparecen en `/api/schema/` y `/api/docs/`.
- **Flag de entorno `INTEGRACION_TICKETERA_ENABLED`** (`config/settings.py`,
  leído con `_safe_bool_env`, **default `True`**). Es un kill-switch: cuando
  está en `False` ambos endpoints responden `503 Service Unavailable` con
  `{"error": "integration_disabled", "message": "..."}` sin tocar la base.
  Documentado en `.env.example`.

## Impacto esperado

- Con el flag en `True` (default) los endpoints operan igual que hoy: no se
  requiere ningún cambio de configuración para mantener el comportamiento
  actual.
- Con el flag en `False` la integración queda apagada de forma uniforme y
  explícita (503) sin desmontar rutas ni afectar al resto de la API.
- El gate se evalúa dentro de `post()`, después de la verificación de API Key:
  un request sin credenciales sigue recibiendo `403`. La Ticketera (que siempre
  envía API Key) recibe el `503` cuando está deshabilitado.
- No cambia el contrato de los endpoints ni el resto del sistema.

## Validación

- `black --check` sobre los archivos modificados.
- Test nuevo `integracion/tests.py`: con el flag deshabilitado ambos endpoints
  devuelven `503` con el body esperado; con el flag habilitado el alta opera
  normalmente (`201`).
- **Sin validar localmente:** `manage.py spectacular` y la suite `pytest`
  completa, por entorno Python local roto (ImportError `punycode`) y Docker
  apagado. Queda delegado a la CI del PR.

## Riesgos y rollback

- **Riesgo principal:** que el flag quede en `False` por error en un entorno
  donde la Ticketera espera operar, devolviendo `503` a todos los logins.
  Mitigación: default `True` y variable documentada en `.env.example`.
- **Rollback:** setear `INTEGRACION_TICKETERA_ENABLED=true` (o quitar la
  variable, ya que el default es `True`). Para revertir el código, las
  anotaciones de schema y el gate son aislados en `integracion/api_views.py` y
  la línea de `config/settings.py`.
