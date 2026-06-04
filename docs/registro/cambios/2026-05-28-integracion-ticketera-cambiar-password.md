# 2026-05-28 - Cierre del ciclo de contraseña temporal (Ticketera)

## Contexto

- Endpoints server-to-server de la integración con la Ticketera
  (`ticketera/api_views.py`), protegidos por API Key. Arquitectura y contratos
  en
  [docs/registro/decisiones/2026-05-27-integracion-ticketera.md](../decisiones/2026-05-27-integracion-ticketera.md).
- El ciclo de "contraseña temporal" estaba a medias: el alta marcaba
  `must_change_password=True` y `verificar` lo informaba, pero **no había forma
  vía la integración** de fijar la contraseña definitiva y bajar el flag. Los
  mecanismos existentes no aplican a este canal: `PasswordChangeRequiredViewSet`
  exige Token DRF (la integración no emite tokens), el
  `FirstLoginPasswordChangeMiddleware` exime `/api/` y exige sesión web, y el
  reset por email es otro flujo.

## Cambios aplicados

- **Nuevo endpoint `POST /api/ticketera/auth/cambiar-password/`**
  (`HasAPIKey`, `TicketeraAuthCambiarPasswordView`). Flujo:
  1. Gate `TICKETERA_ENABLED` (igual que los otros dos endpoints;
     `503` si está apagado).
  2. Rate limit `hit_rate_limit` con scope propio `ticketera_cambiar_password`,
     identidad `f"{ip}:{username}"`, `limit=10`, `window_seconds=300` (mismo
     patrón que `verificar`).
  3. `authenticate(username, current_password)`; si falla o el usuario está
     inactivo ⇒ `401 { error: "invalid_credentials" }`.
  4. Valida `new_password` con `password_validation.validate_password(...,
     user)` y rechaza que sea igual a `current_password` ⇒ `400 { new_password:
     [...] }`.
  5. Dentro de `audit_context(source="ticketera",
     extra={"remote_source": source})`, reutiliza
     `users.services_auth.change_password_for_authenticated_user` (no se duplica
     la lógica) y emite un `LogEntry` `UPDATE` explícito con la contraseña
     redactada.
  6. `200 { changed: true, must_change_password: false }`.
- **`TicketeraUsuarioCreateView` ahora setea `initial_password_expires_at`** en
  el alta (`now + timedelta(hours=INITIAL_PASSWORD_MAX_AGE_HOURS)`), para que la
  temporal de Ticketera expire igual que en el flujo PWA/web. **El contrato de
  `/usuarios/` no cambia** (sigue devolviendo `{ id, username, email }`).
- **Serializers nuevos** en `ticketera/api_serializers.py`:
  `TicketeraAuthCambiarPasswordSerializer` (request) y
  `TicketeraAuthCambiarPasswordResponseSerializer` (response 200), anotados en
  `@extend_schema` (aparecen en `/api/schema/` y `/api/docs/`).
- **Ruta** `auth/cambiar-password/` en `ticketera/api_urls.py`.

## Decisiones

- **Expiración de la temporal en el alta — DEFAULT: SÍ (aplicado).** Se setea
  `initial_password_expires_at` para alinear la temporal de Ticketera con el
  resto del sistema. **Interacción conocida:** ese campo se enforcea en el login
  del backoffice web (`users.forms.BackofficeAuthenticationForm`); un usuario de
  Ticketera con la temporal vencida quedaría bloqueado **en el backoffice web**
  (no en su flujo normal contra la Ticketera). Solo afecta altas nuevas.
- **Bloqueo por flag/expiración en `verificar` — DEFAULT: NO (no activado).**
  `verificar` sigue informando `must_change_password` sin bloquear. El dato de
  expiración queda disponible por si el equipo decide enforcearlo; no se activa
  sin confirmación para no cambiar el comportamiento observable de `verificar`.
- **`cambiar-password` no exige `must_change_password=True` ni rechaza por
  expiración.** Conocer la contraseña actual habilita fijar una nueva aun con la
  inicial vencida (recuperación), y el cambio siempre deja
  `must_change_password=false`.
- **`LogEntry` explícito.** `password` está en `excluded_fields` del modelo
  `Usuario` en auditlog y `Profile` no es trackeado, así que el `save` no genera
  diff; se registra un `UPDATE` redactado (`{"password": ["***", "***"]}`),
  mismo recurso que el `ACCESS` de `verificar` con `last_login`.

## Impacto esperado

- La Ticketera puede cerrar el ciclo: tras un `cambiar-password` exitoso, un
  `verificar` posterior devuelve `must_change_password=false`.
- `current_password` incorrecta ⇒ `401` sin tocar la base; `new_password` débil
  o igual a la actual ⇒ `400` sin tocar la base.
- El cambio queda en el audittrail con `source="ticketera"`.
- Sin cambios en los contratos de `/usuarios/` ni `/verificar/`.

## Validación

- `black --check` sobre `ticketera/api_views.py`,
  `ticketera/api_serializers.py`, `ticketera/api_urls.py`,
  `ticketera/tests.py` y `tests/test_ticketera.py`.
- Tests nuevos:
  - `tests/test_ticketera.py`: ciclo completo (200 + verificar
    posterior con `must_change_password=false`), `401` por current incorrecta y
    por usuario inactivo (sin cambios), `400` por débil y por igual a la actual
    (sin cambios), `429` en el intento 11, auditoría con source Ticketera, y la
    URL agregada al test parametrizado de "sin API Key".
  - `ticketera/tests.py`: `503` con el flag deshabilitado.
- **Sin validar localmente:** `pytest` / `manage.py`. El entorno Python local
  está roto (`ImportError: cannot import name 'punycode'`, mismatch de versión
  de Django) y Docker suele estar apagado. Queda delegado a la CI del PR o a una
  corrida en Docker autorizada.

## Riesgos y rollback

- **Riesgo:** un usuario de Ticketera que use el backoffice web con la temporal
  vencida quedará bloqueado por el enforce de `initial_password_expires_at`.
  Mitigación: no es el flujo de esos usuarios; si molestara, revertir el seteo
  de `initial_password_expires_at` en el alta (los demás cambios son
  independientes).
- **Riesgo:** el rate limit comparte patrón con `verificar` pero usa scope
  propio; no interfiere con el contador de `verificar`.
- **Rollback:** quitar la ruta `cambiar-password` de `ticketera/api_urls.py`
  y la vista/serializers asociados; opcionalmente revertir el seteo de
  `initial_password_expires_at`. Los cambios están acotados a la app
  `ticketera/` (no se modificó `users/services_auth.py`).
