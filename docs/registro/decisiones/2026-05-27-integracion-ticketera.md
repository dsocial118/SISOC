# Decisión: Integración SISOC ↔ Ticketera

**Fecha:** 2026-05-27

---

## Contexto

La Ticketera (Django + PostgreSQL, servidor separado) necesita autenticar a sus
usuarios contra las credenciales gestionadas por SISOC. La Ticketera no debe
almacenar contraseñas propias: SISOC actúa como fuente de verdad.

Se necesitan tres operaciones:

1. **Alta de usuarios** desde la Ticketera hacia SISOC.
2. **Verificación de credenciales** en cada login de la Ticketera.
3. **Cambio de la contraseña temporal** por la definitiva (cierra el ciclo).

---

## Decisión

Crear una app `ticketera/` con tres endpoints REST protegidos por API Key
bajo el prefijo `/api/ticketera/`:

| Método | Ruta | Función |
|---|---|---|
| POST | `/usuarios/` | Crea o reconcilia un usuario (idempotente con `source=ticketera`). |
| POST | `/auth/verificar/` | Verifica credenciales y reporta `must_change_password`. |
| POST | `/auth/cambiar-password/` | Fija la contraseña definitiva y baja `must_change_password` (cierra el ciclo de la temporal). |

### Patrones reutilizados

- **Permiso:** `core.api_auth.HasAPIKey` (sin combinarlo con Token DRF: este
  canal es server-to-server).
- **Rate limit:** `users.rate_limits.hit_rate_limit` (scope
  `ticketera_verificar`, 10 intentos por username cada 5 minutos).
- **Auditoría:** `audittrail.context.audit_context` con
  `source="ticketera"` y `extra={"remote_source": <source>}`.
  El alta de `User` queda registrada vía `auditlog`. En `verificar`, como
  `last_login` está en los campos excluidos del diff (un `save` que solo toca
  ese campo no genera `LogEntry`), se emite un `LogEntry` explícito de tipo
  `ACCESS` sobre el `User` (`LogEntry.objects.log_create`), de modo que el
  acceso queda en el historial con el `source` y el `remote_source` en la
  metadata (`AuditEntryMeta`).
- **Creación de usuario:** `User.objects.create_user()` + `Profile.get_or_create()`
  siguiendo el patrón de `users/services_pwa.py`.

### Cambio de modelo

Se agrega `Profile.source` (CharField, `max_length=50`, default `"sisoc"`)
para distinguir el origen del alta. Valores esperados iniciales:

- `"sisoc"` (default — usuarios creados desde el backoffice).
- `"ticketera"` — usuarios provisionados por la Ticketera.

El campo es informativo y se usa para la lógica idempotente del endpoint de
alta (si el username existe con `source=ticketera`, se responde 200 con los
datos del usuario; si existe con otro origen se responde 409).

Migración: `users/migrations/0031_profile_source.py`.

---

## Decisiones explícitas (no cuestionar)

- **Sin OAuth/JWT.** API Key + verificación de credenciales por endpoint es
  suficiente para el caso server-to-server.
- **Sin Token DRF en `verificar`.** La sesión la administra la Ticketera con
  su propio mecanismo; SISOC solo confirma la validez.
- **Sin sincronización de roles ni permisos.** Los roles viven exclusivamente
  en la Ticketera.
- **Sin `Profile.temporary_password_plaintext`.** Se usa
  `must_change_password=True` para forzar el cambio en el próximo login.
- **El campo `source` del body** es informativo: no afecta la lógica de
  permisos ni se valida contra un enum cerrado.
- **Caída de SISOC ⇒ login de Ticketera falla.** Comportamiento aceptado
  para evitar fragmentar la fuente de verdad.
- **Usuarios ciudadanos quedan fuera de este alcance.** Se autentican vía
  Mi Argentina.

---

## Contratos

### POST `/api/ticketera/usuarios/`

Request:

```json
{
  "username": "juan.perez",
  "email": "juan.perez@ejemplo.gob.ar",
  "first_name": "Juan",
  "last_name": "Pérez",
  "password": "ContraseñaTemporal1!",
  "source": "ticketera"
}
```

Respuestas:

- `201 Created` — alta nueva: `{ id, username, email }`.
- `200 OK` — usuario ya existía con `source=ticketera` (idempotente):
  `{ id, username, email }`.
- `409 Conflict` — username ocupado por otro origen:
  `{ "error": "username_taken", "message": "..." }`.

### POST `/api/ticketera/auth/verificar/`

Request:

```json
{
  "username": "juan.perez",
  "password": "ContraseñaIngresada",
  "source": "ticketera"
}
```

Respuestas:

- `200 OK` — `{ valid: true, must_change_password, user: { ... } }`.
- `401 Unauthorized` — `{ valid: false, error: "invalid_credentials" }`.
- `429 Too Many Requests` — `{ error: "too_many_attempts", message: "..." }`.

### POST `/api/ticketera/auth/cambiar-password/`

Request:

```json
{
  "username": "juan.perez",
  "current_password": "ContraseñaTemporal1!",
  "new_password": "ContraseñaDefinitiva9!",
  "source": "ticketera"
}
```

Respuestas:

- `200 OK` — `{ changed: true, must_change_password: false }`.
- `400 Bad Request` — `new_password` débil o igual a la actual:
  `{ "new_password": ["<motivo>", ...] }`.
- `401 Unauthorized` — `current_password` incorrecta o usuario inactivo:
  `{ error: "invalid_credentials" }`.
- `429 Too Many Requests` — `{ error: "too_many_attempts", message: "..." }`.
- `503 Service Unavailable` — integración deshabilitada por flag.

---

## Cierre del ciclo de contraseña temporal (2026-05-28)

### Problema

El ciclo de "contraseña temporal" quedaba a medias: el alta marcaba
`must_change_password=True` y `verificar` lo informaba, pero **no había forma,
vía la integración, de que el usuario fijara su contraseña definitiva y bajara
el flag**. Los mecanismos existentes no aplican a este canal:

- `PasswordChangeRequiredViewSet` exige `TokenAuthentication` +
  `IsAuthenticated`, y la integración **no emite Token DRF** (decisión de
  diseño: la sesión la maneja la Ticketera).
- `FirstLoginPasswordChangeMiddleware` exime `/api/` y exige sesión web.
- El reset por email es otro flujo (requiere mailbox del usuario).

### Decisión

Agregar `POST /api/ticketera/auth/cambiar-password/` (`HasAPIKey`,
server-to-server) que cierra el ciclo:

1. **Rate limit** con `users.rate_limits.hit_rate_limit` (scope propio
   `ticketera_cambiar_password`, identidad `f"{ip}:{username}"`, `limit=10`,
   `window_seconds=300` — mismo patrón que `verificar`).
2. `authenticate(username, current_password)`; si falla o el usuario está
   inactivo ⇒ `401 { error: "invalid_credentials" }` (no distingue inexistente
   de credenciales malas, igual que `verificar`).
3. Validación de `new_password`:
   - `django.contrib.auth.password_validation.validate_password(new_password,
     user)` (usa `AUTH_PASSWORD_VALIDATORS`); si falla ⇒ `400 { new_password:
     [...] }`.
   - `new_password` **no puede ser igual** a `current_password` ⇒ `400 {
     new_password: ["La nueva contraseña debe ser distinta de la actual."] }`.
4. La mutación reutiliza
   `users.services_auth.change_password_for_authenticated_user` (no se duplica
   la lógica), que setea la contraseña y limpia `must_change_password`,
   `password_changed_at`, `initial_password_expires_at`,
   `password_reset_requested_at` y `temporary_password_plaintext`.
5. Corre dentro de `audit_context(source="ticketera",
   extra={"remote_source": source})`. Como **`password` está en los
   `excluded_fields` del modelo `Usuario` en auditlog** y `Profile` no es un
   modelo trackeado, un `save` de la contraseña no genera diff: se emite un
   `LogEntry` `UPDATE` explícito con el valor redactado
   (`changes={"password": ["***", "***"]}`), mismo recurso que el `ACCESS` de
   `verificar` para `last_login`.

**No requiere `must_change_password=True`.** El endpoint sirve tanto para cerrar
la temporal como para un cambio voluntario; en ambos casos deja
`must_change_password=false`. **No rechaza por expiración** de la temporal: aun
con la inicial vencida, conocer la contraseña actual permite recuperarse fijando
una nueva (coherente con la decisión de no bloquear, abajo).

### Expiración de la temporal en el alta — DEFAULT: SÍ (aplicado)

El alta (`/usuarios/`) ahora setea
`initial_password_expires_at = now + timedelta(hours=INITIAL_PASSWORD_MAX_AGE_HOURS)`,
para que la temporal de Ticketera expire igual que en el flujo PWA/web (ver
`generate_temporary_password_for_user`). **El contrato de `/usuarios/` no
cambia** (sigue respondiendo `{ id, username, email }`).

- **Interacción conocida:** `initial_password_expires_at` se **enforcea en el
  login del backoffice web** (`users.forms.BackofficeAuthenticationForm.confirm_login_allowed`:
  si `must_change_password` y la fecha venció, rechaza con
  `initial_password_expired`). Un usuario provisionado por Ticketera que intente
  ingresar al backoffice web con la temporal vencida quedaría bloqueado. No es
  el flujo de estos usuarios (operan contra la Ticketera, no el backoffice) y
  solo afecta a altas nuevas; los registros previos conservan `NULL`.
- **`verificar` y `cambiar-password` NO enforcean la expiración** (ver
  siguiente decisión): el dato queda disponible por si el equipo decide
  activarlo, sin bloquear hoy.

### Bloqueo por flag pendiente en `verificar` — DEFAULT: NO (no activado)

`verificar` sigue **informando** `must_change_password` sin bloquear por flag
pendiente ni por expiración. Si el equipo lo pide, se podría rechazar cuando la
temporal venció (`initial_password_expires_at < now`). **Queda documentado como
decisión; no se activa sin confirmación**, para no cambiar el comportamiento
observable de `verificar` (sus contratos `200/401/429` se preservan).

---

## Endurecimiento de seguridad/robustez (2026-05-28)

Cuatro correcciones sobre los endpoints **sin cambiar los contratos existentes**
(`200`/`201`/`401`/`409`/`429` conservan su shape). Cambio asociado:
[docs/registro/cambios/2026-05-28-integracion-ticketera-hardening.md](../cambios/2026-05-28-integracion-ticketera-hardening.md).

1. **Carrera en el alta resuelta sin `500`.** `create_user` se envuelve en
   `try/except IntegrityError` (patrón de `users/services_pwa.py`). Si dos
   requests con el mismo username compiten, el perdedor recibe el `IntegrityError`
   de la constraint única, vuelve a consultar y responde con la misma lógica del
   camino normal: `200` si el ganador quedó con `source="ticketera"`, `409` si
   quedó con otro origen. Nunca `500`.

2. **Existencia/conflicto case-insensitive, sin normalizar el username
   almacenado.** El chequeo pasa de `username=` a `username__iexact=` (igual que
   `create_operador_for_comedor`), para que `"Juan.Perez"` y `"juan.perez"` no
   esquiven la idempotencia ni el `409`. **Decisión:** NO se normaliza/lowercasea
   el username al guardar; se persiste tal cual se recibe. Motivo: `verificar`
   usa `authenticate()` con el backend default (`ModelBackend`, case-sensitive en
   username); normalizar el almacenamiento rompería el login cuando la Ticketera
   envía el username con su capitalización original. La unicidad efectiva entre
   variantes de capitalización se apoya en la collation case-insensitive de MySQL
   (default), que dispara el `IntegrityError` del punto 1 ante un duplicado por
   mayúsculas/minúsculas.

3. **Validación de fortaleza de contraseña en el alta.** Antes de crear el
   usuario se corre `django.contrib.auth.password_validation.validate_password`
   (usa `AUTH_PASSWORD_VALIDATORS`) contra un `User` no persistido con
   username/email/nombre, para habilitar `UserAttributeSimilarityValidator`. Si
   falla, responde `400` con `{ "password": [<mensajes>] }` y **no** crea el
   usuario. Se ubica en el camino de creación (después de resolver
   idempotencia/conflicto) para no alterar los shapes `200`/`409`.

4. **Rate limit de `verificar` con IP en la identidad.** La identidad pasa de
   `username` a `f"{ip}:{username}"` (`ip = request.META.get("REMOTE_ADDR",
   "anon")`), mismo patrón que `PasswordResetRequestViewSet`. Se mantienen
   `scope`/`limit`/`window` (`ticketera_verificar`, 10, 300 s).
   **Decisión: NO se agrega un contador por-IP separado.** Este endpoint es
   server-to-server detrás de API Key: el tráfico legítimo de la Ticketera llega
   desde una única IP (o un proxy compartido) en nombre de muchos usuarios; un
   tope por-IP estrangularía los logins legítimos (incidente de disponibilidad,
   contrario a la decisión "caída de SISOC ⇒ login falla" que prioriza la
   disponibilidad de la verificación). El perímetro real contra rotación de
   usernames es la API Key (`HasAPIKey`): sin ella el endpoint no es alcanzable.
   Un throttling por origen, de quererse, debería keyearse por identidad de
   cliente/API Key, no por `REMOTE_ADDR`.

### Contrato afectado

- `POST /usuarios/` agrega `400 Bad Request` por contraseña débil:
  `{ "password": ["<motivo 1>", ...] }`. (El `400` por payload inválido del
  serializer ya existía; este reutiliza ese mismo status.)

---

## Archivos tocados

- `ticketera/__init__.py`, `ticketera/apps.py`
- `ticketera/api_serializers.py`
- `ticketera/api_views.py`
- `ticketera/api_urls.py`
- `users/models.py` — campo `Profile.source`
- `users/migrations/0031_profile_source.py`
- `config/settings.py` — alta de la app en `INSTALLED_APPS`
- `config/urls.py` — alta de la ruta `/api/ticketera/`
- `docs/registro/decisiones/2026-05-27-integracion-ticketera.md` (este archivo)

### Cierre del ciclo de contraseña temporal (2026-05-28)

- `ticketera/api_serializers.py` — `TicketeraAuthCambiarPasswordSerializer` y
  `TicketeraAuthCambiarPasswordResponseSerializer`.
- `ticketera/api_views.py` — `TicketeraAuthCambiarPasswordView`;
  `initial_password_expires_at` en `TicketeraUsuarioCreateView`.
- `ticketera/api_urls.py` — ruta `auth/cambiar-password/`.
- `tests/test_ticketera.py`, `ticketera/tests.py` — tests del
  nuevo endpoint (happy path/ciclo, `401`/`400`/`429`, auditoría, `503` por flag).
- `docs/registro/cambios/2026-05-28-integracion-ticketera-cambiar-password.md`.
- Reutiliza sin modificar: `users.services_auth.change_password_for_authenticated_user`.
