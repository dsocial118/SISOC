# Plan — Extender API Ticketera: editar usuarios + solicitar reset de contraseña

**Fecha:** 2026-06-08
**Estado:** Borrador para revisión humana. **No** implementar hasta OK.

---

## 1. Contexto y objetivo

La integración server-to-server con la Ticketera ([ADR 2026-05-27](../registro/decisiones/2026-05-27-integracion-ticketera.md), [hardening 2026-05-28](../registro/cambios/2026-05-28-integracion-ticketera-hardening.md)) hoy expone tres endpoints: alta/reconciliación de usuarios, verificación de credenciales y cambio de la temporal por la definitiva. La Ticketera necesita además poder **(1) editar datos básicos del usuario** (email/nombre/apellido) que provisionó y **(2) iniciar el reset de contraseña** de usuarios suyos cuando el portador olvida la clave o pide regenerarla. Este plan diseña ambas extensiones manteniendo los contratos de los tres endpoints actuales y reutilizando los patrones existentes (HasAPIKey, rate limit, `audit_context`, `_is_ticketera_source`).

---

## 2. Decisiones pendientes (con recomendación marcada)

> El humano revisa y confirma este bloque **antes** de pasar a código.

### 2.1 Capacidad 1 — PATCH usuarios

#### D1. Forma de la URL para PATCH

- **A. `PATCH /api/ticketera/usuarios/<username>/` (recomendada)** — REST estándar, drf-spectacular documenta el path param explícito, deja `name="ticketera-usuarios-detail"`. El POST de alta sigue en `/usuarios/`.
- B. `PATCH /api/ticketera/usuarios/` con `username` en body. Mantiene el shape del POST, pero "edit by body" es no idiomático en DRF/OpenAPI y arrastra branching innecesario sobre el mismo path.

**Por qué A:** REST estándar y separación clara recurso/datos. Path param permite cobertura sencilla del 404 anti-enumeration. Costo: una nueva URL pero la app ya tiene tres → no se rompe el estilo `ticketera-*`.

#### D2. 403 vs 404 cuando el usuario existe pero no es Ticketera

> El brief decía "decisión ya tomada: 403". Evalúo el tradeoff igual.

- **A. 403 `{ "error": "user_not_ticketera" }` (recomendada, respeta lo ya decidido).** Pros: la Ticketera distingue "no existe" de "no te pertenece" → soporte operativo más simple. Contras: permite enumeration de usernames SISOC al portador de la API Key.
- B. 404 idéntico al "no existe". Anti-enumeration estricta. Contras: opaco para soporte; la Ticketera no sabe si bañaba en datos o si chocó con un username SISOC homónimo.

**Por qué A:** el canal es S2S detrás de API Key (no público), el universo "enumerable" es muy chico y la Ticketera ya conoce sus altas. La operatividad pesa más que la pseudoanonimidad. Documentar en el ADR el tradeoff.

#### D3. Campos editables

- **email**: SÍ. Decisión clave: ¿unicidad? **Recomendado: NO** (mantener el comportamiento actual de SISOC, que permite emails repetidos en `auth_user`). Imponer unicidad solo en este canal abre divergencia: usuarios provisionados desde el backoffice podrían ya colisionar y el PATCH no podría reparar el suyo. Si la Ticketera lo necesita, pedir un campo aparte (`email_normalizado`) o tratar como issue separado.
- **first_name, last_name**: SÍ.
- **username**: NO. Cambiarlo rompe `authenticate()` (ModelBackend case-sensitive) y obliga a re-emitir credenciales. Si en el futuro hace falta, será una operación distinta (rename con migración explícita).
- **password**: NO. Tiene su endpoint dedicado `/auth/cambiar-password/` (y el `/auth/solicitar-reset-password/` de la capacidad 2). Mezclar canales borra trazabilidad.
- **is_active**: **NO en este MVP (recomendada).** Permitir bajar `is_active` desde la Ticketera obliga a decidir qué pasa con sesiones web, `must_change_password` y reactivaciones; introduce un canal de desactivación que hoy solo existe en el backoffice. Si la Ticketera lo pide, se evalúa por separado.
- **source**: nunca editable desde la API.

#### D4. Idempotencia del PATCH

- **Recomendada:** aplicar solo los cambios reales (`update_fields` derivado de los campos que llegaron y que difieren del valor actual). Si nada cambia, `save()` no se invoca y auditlog no genera `LogEntry`. Respuesta `200 OK` con el snapshot del usuario.
- Justificación: el patrón ya está implícito en `_existing_user_response` del POST (responder el snapshot existente sin tocar nada). Evita ruido en `auditlog`/`AuditEntryMeta`.

#### D5. Lookup case-insensitive del path param

- **Recomendada:** mismo criterio que el POST (`username__iexact`). El `<username>` del path se resuelve con `iexact` para no esquivar el 404 por mayúsculas/minúsculas; el username almacenado **no se normaliza** y la respuesta devuelve el username canónico de la fila.

#### D6. ¿Aceptar PATCH vacío?

- **Recomendada:** sí → `200 OK` con el snapshot actual (idempotente). Refleja el mismo principio que el alta idempotente.

### 2.2 Capacidad 2 — Reset de contraseña

#### D7. Diseño del reset (A vs B)

- **A. La Ticketera dispara el reset y SISOC manda el mail con link a `password_reset_confirm` (recomendada para esta entrega).** Reusa `request_password_reset_for_email`/`request_password_reset_for_username` tal cual; cero superficie de cierre. El usuario completa el reset por web (UX coherente con el reset PWA/backoffice). Pros: mínima superficie nueva, sin manejo de tokens en la integración. Contras: la UX termina en SISOC; la Ticketera no puede ofrecer una pantalla nativa para fijar la nueva clave.
- B. Endpoint devuelve `{uid, token}` + nuevo `POST /api/ticketera/auth/confirmar-reset-password/` que valida `(uid, token)` con `default_token_generator` y aplica vía `confirm_password_reset`. Pros: UX nativa Ticketera. Contras: doble endpoint, token con TTL Django (`PASSWORD_RESET_TIMEOUT`) en tránsito, mayor superficie para logs/leaks; obliga a definir si la Ticketera arma el mail o si SISOC los manda igual.

**Por qué A:** alinea con el "principio de mínima superficie" del ADR, no agrega un canal de tokens fuera de SISOC y reusa el link que ya validamos en producción. Si más adelante la Ticketera necesita UX nativa de reset, se agrega B como follow-up (sigue siendo aditivo, no breaking). En la sección 3.2 documento ambas opciones para que el humano decida ya.

#### D8. Identificación del usuario en el request

- **Recomendada:** `username` o `email` (exclusivos) en el body, mismo patrón que `PasswordResetRequestSerializer` ([users/api_serializers.py:134-161](../../users/api_serializers.py)). Validación equivalente: exactamente uno de los dos.

#### D9. Filtro por origen

- **A. Solo usuarios con `_is_ticketera_source(profile.source)` (recomendada).** Coherente con el espíritu del canal: la Ticketera opera sobre sus propios usuarios; un reset cross-origen entre canales es sospechoso. El 200 genérico anti-enumeration cubre cualquier filtro silencioso.
- B. Cualquier usuario activo. Más permisivo (la Ticketera podría disparar reset de usuarios SISOC), pero abre un canal lateral con API Key.

**Por qué A:** la API Key es un perímetro fuerte, pero darle palanca para iniciar reset de usuarios de otros canales acopla sin necesidad. Operativamente la Ticketera solo conoce sus usuarios.

#### D10. Anti-enumeration

- **Recomendada:** `200 OK` SIEMPRE con `{"detail": "Si el usuario existe en el sistema, se registró la solicitud de reseteo."}` (texto idéntico al de la API web actual). No 401/404. Igual que [users/api_views.py:231-238](../../users/api_views.py).

#### D11. Rate limit

- **Recomendada:** scope `ticketera_solicitar_reset`, `limit=5`, `window_seconds=900`, identidad `f"{ip}:{username or email lowercased}"`. Mismo perfil que `password_reset_request` (5/15 min) — el reset es más sensible que `verificar` y debe ser más restrictivo. La identidad incluye IP por consistencia con el resto de la app; no se agrega contador por-IP separado por la misma razón documentada en el hardening 2026-05-28.

#### D12. Auditoría del reset

- **Recomendada:** emitir `LogEntry` explícito con `action=ACCESS` sobre el `User` (mismo recurso que `verificar`), con `changes={"password_reset_requested": [None, <isoformat>]}` y `audittrail_source="ticketera"`, dentro de `audit_context(source="ticketera", extra={"remote_source": ...})`. Hoy el flujo web solo loguea con `logger.info`; para este canal queremos rastro en auditlog ya que es server-to-server y no hay sesión que correlacionar.
- Cuando no exista el usuario o el origen no sea Ticketera: **no se emite LogEntry** (no se confirma la existencia ni para el log).

#### D13. Compatibilidad con `must_change_password`

- En **Opción A** el ciclo termina en `confirm_password_reset` ([users/services_auth.py:119](../../users/services_auth.py)), que ya baja `must_change_password`, limpia `initial_password_expires_at`, `password_reset_requested_at` y `temporary_password_plaintext`. **Nada que tocar.**
- En Opción B el endpoint `confirmar` reusa la misma función. **Nada que tocar.**

---

## 3. Diseño detallado

### 3.1 Capacidad 1 — PATCH `/api/ticketera/usuarios/<username>/`

#### Endpoint

- Método: `PATCH`.
- Path: `/api/ticketera/usuarios/<str:username>/` — `name="ticketera-usuarios-detail"`.
- Auth: `HasAPIKey` (mismo perímetro que el POST).
- Flag: `settings.TICKETERA_ENABLED` (503 si está off, vía `_ticketera_disabled_response`).
- Mismo `tags=["Ticketera"]` en `@extend_schema`.

#### Request body

```json
{
  "email": "nuevo@ejemplo.gob.ar",
  "first_name": "Juan Pablo",
  "last_name": "Pérez",
  "source": "ticketera-qa"
}
```

- Todos los campos opcionales.
- `source`: informativo (igual semántica que el POST: alimenta `extra.remote_source` para auditoría; **no** se persiste sobre `profile.source` en este endpoint).
- Cualquier otro field se ignora (DRF default; no se valida exclusión estricta).

#### Response shapes

- **200** — snapshot canónico del usuario:
  ```json
  {"id": 17, "username": "juan.perez", "email": "...", "first_name": "...", "last_name": "..."}
  ```
- **400** — payload inválido (email malformado, tipos incorrectos) con la shape estándar de DRF (`{"email": ["Enter a valid email address."]}`).
- **403** — `{"error": "user_not_ticketera", "message": "El usuario existe pero no fue provisionado por la Ticketera."}` (cuando el lookup `iexact` matchea pero `profile.source` no pasa `_is_ticketera_source`).
- **404** — `{"error": "user_not_found", "message": "No existe un usuario con ese username."}`.
- **503** — integración off (igual shape que los endpoints actuales).

#### Serializer

- Nuevo `TicketeraUsuarioPatchSerializer` en [ticketera/api_serializers.py](../../ticketera/api_serializers.py):
  - `email = serializers.EmailField(max_length=254, required=False)`
  - `first_name = serializers.CharField(max_length=150, allow_blank=True, required=False)`
  - `last_name = serializers.CharField(max_length=150, allow_blank=True, required=False)`
  - `source = serializers.CharField(max_length=50, required=False, default="ticketera")`
  - Pylint disable abstract-method (mismo patrón que el resto del módulo).
- **No** reusa `TicketeraUsuarioCreateSerializer` para no arrastrar `username/password` como required ni para acoplar dos contratos distintos.
- Response serializer nuevo `TicketeraUsuarioDetailSerializer` (id, username, email, first_name, last_name) — los actuales devuelven solo `(id, username, email)` y queremos exponer nombres en la respuesta del PATCH para que la Ticketera confirme.

#### Lógica de la view (prosa)

`TicketeraUsuarioUpdateView(APIView)`:

1. Si `not settings.TICKETERA_ENABLED` → 503.
2. Validar serializer (raise_exception=True).
3. Resolver `existing = User.objects.select_related("profile").filter(username__iexact=username_path).first()`.
4. Si `existing is None` → 404.
5. Si no `_is_ticketera_source(existing.profile.source or "")` → 403.
6. Construir `update_fields` recorriendo los fields del serializer que llegaron y comparando contra el valor actual. Si no cambia ninguno → 200 con el snapshot.
7. Dentro de `with audit_context(source="ticketera", extra={"remote_source": source}): with transaction.atomic():` aplicar `setattr` + `existing.save(update_fields=[...])`. **Solo** se persisten los fields que cambiaron.
8. Responder 200 con `TicketeraUsuarioDetailSerializer(existing).data`.

#### Auditoría

- `auditlog` registra el `UPDATE` de `auth_user` automáticamente con el diff de los campos cambiados (los campos editables `email/first_name/last_name` **no** están en `excluded_fields` del Usuario — ver [audittrail/constants.py:108-112](../../audittrail/constants.py): solo `password` está excluido fijo y `last_login` opcional).
- **No** se requiere `LogEntry` explícito (el diff lo captura `auditlog`).
- `audit_context` inyecta `source="ticketera"` y `extra={"remote_source": source}` (siempre, aunque no haya cambios — pero no llegará a tocar nada si no hay diff).

#### Rate limit

- **No se aplica** rate limit a este endpoint en el MVP. Justificación: el riesgo es bajo (no toca credenciales ni revela info sensible), el canal está protegido por API Key y la Ticketera no tiene incentivo para spammear. Si aparece abuso, se agrega scope `ticketera_editar_usuario` con `(limit=20, window=300)` por `f"{ip}:{username}"`.

#### Errores y códigos (resumen)

| Status | Cuándo | Body |
|---|---|---|
| 200 | Edición aplicada o idempotente | snapshot del usuario |
| 400 | Email malformado / payload inválido | shape DRF default |
| 403 | Existe con origen no Ticketera | `{"error": "user_not_ticketera", "message": "..."}` |
| 404 | No existe | `{"error": "user_not_found", "message": "..."}` |
| 503 | `TICKETERA_ENABLED=False` | `{"error": "integration_disabled", "message": "..."}` |

### 3.2 Capacidad 2 — POST `/api/ticketera/auth/solicitar-reset-password/`

#### Endpoint

- Método: `POST`.
- Path: `/api/ticketera/auth/solicitar-reset-password/` — `name="ticketera-auth-solicitar-reset-password"`.
- Auth: `HasAPIKey`. Flag `TICKETERA_ENABLED`.
- `tags=["Ticketera"]`.

#### Request body

```json
{
  "username": "juan.perez",
  "source": "ticketera"
}
```

o

```json
{
  "email": "juan.perez@ejemplo.gob.ar",
  "source": "ticketera"
}
```

Exactamente uno de `username` o `email` (excluyentes). `source` informativo.

#### Response shapes

- **200** SIEMPRE: `{"detail": "Si el usuario existe en el sistema, se registró la solicitud de reseteo."}` (string idéntico al de la API web).
- **400** — solo cuando faltan ambos identificadores o llegan los dos (validación de serializer). Shape DRF default.
- **429** — `{"error": "too_many_attempts", "message": "Demasiados intentos. Esperá unos minutos."}`.
- **503** — integración off.

> No se devuelve 401/404: anti-enumeration absoluta.

#### Serializer

- Nuevo `TicketeraSolicitarResetSerializer`:
  - `username = serializers.CharField(max_length=150, required=False)`
  - `email = serializers.EmailField(max_length=254, required=False)`
  - `source = serializers.CharField(max_length=50, required=False, default="ticketera")`
  - `validate()`: replicar el XOR de `PasswordResetRequestSerializer` ([users/api_serializers.py:147-161](../../users/api_serializers.py)) — si llegan ambos o ninguno, `ValidationError`.

#### Lógica de la view (prosa) — Opción A (recomendada)

`TicketeraSolicitarResetPasswordView(APIView)`:

1. Si `not settings.TICKETERA_ENABLED` → 503.
2. Validar serializer.
3. Aplicar `hit_rate_limit(scope="ticketera_solicitar_reset", identity=f"{ip}:{username_or_email_lower}", limit=5, window_seconds=900)` → 429 si supera.
4. Resolver `user`:
   - Si vino `username`: `User.objects.filter(username__iexact=username, is_active=True).select_related("profile").first()`.
   - Si vino `email`: `User.objects.filter(email__iexact=email, is_active=True).select_related("profile").order_by("id").first()` (criterio determinístico ante duplicados de email, que SISOC permite).
5. Si `user` existe y `_is_ticketera_source(getattr(user.profile, "source", ""))`:
   - Dentro de `audit_context(source="ticketera", extra={"remote_source": source})`:
     - Llamar a `request_password_reset_for_email(email=user.email, request=request)` cuando el usuario tiene email; esto cubre el caso por email **y** el caso por username (en ese último, leemos el email del usuario resuelto). **No** se llama a `request_password_reset_for_username` (es un canal mobile distinto que solo setea `password_reset_requested_at` sin mandar mail).
     - Si el usuario no tiene email registrado, no se manda nada (logger.warning) — la respuesta sigue siendo 200 anti-enumeration.
     - Emitir `LogEntry.objects.log_create(user, action=ACCESS, changes={"password_reset_requested": [None, now.isoformat()]}, actor=user, additional_data={"audittrail_source": "ticketera", "audittrail_context": {"remote_source": source}})`.
6. Responder 200 con el mensaje genérico (existe / no existe / origen no Ticketera son indistinguibles para el cliente).

#### Lógica de la view (prosa) — Opción B (si el humano la elige en lugar de A)

`TicketeraSolicitarResetPasswordView` (igual a 1-4 anteriores) pero devuelve `{ "uid": <urlsafe_base64>, "token": <token> }` cuando `user` cumple los filtros. Anti-enumeration: cuando el usuario no cumple, devolver un par `uid/token` falso desbalancearía la respuesta → preferible mantener 200 con `{"detail": "..."}` cuando no aplica (asimétrico observable). Esta asimetría es el costo de B y otra razón para preferir A.

Si se elige B, agregar un segundo endpoint `POST /api/ticketera/auth/confirmar-reset-password/` con:
- Body `{ "uid", "token", "new_password", "source" }`.
- Validación de fortaleza con `password_validation.validate_password(new_password, user)`.
- Reusar `confirm_password_reset(uid, token, new_password)` ([users/services_auth.py:119](../../users/services_auth.py)) — que ya limpia `must_change_password`, `initial_password_expires_at`, `password_reset_requested_at` y `temporary_password_plaintext`.
- Tras el reset, `Token.objects.filter(user=user).delete()` (mismo patrón que [users/api_views.py:279](../../users/api_views.py)).
- Rate limit propio scope `ticketera_confirmar_reset` (limit=10, window=900) por `ip` (no por uid, que es el secreto que estamos defendiendo).
- Respuestas: 200 `{"changed": true}`; 400 `{"detail": "Token inválido o expirado."}`; 429; 503.

> El plan **recomienda Opción A** y la implementa por defecto. Opción B queda diseñada acá pero **no se implementa** salvo decisión explícita del humano.

#### Auditoría

- Opción A: ver paso 5; un `LogEntry ACCESS` cuando se dispara el envío, con `audittrail_source="ticketera"`.
- Opción B (si se elige): el `confirmar` invoca `set_password` + `save(update_fields=["password"])` que **no** genera diff (password excluido). Replicar el patrón de `cambiar-password` y emitir `LogEntry UPDATE` con `changes={"password": ["***", "***"]}`.

#### Rate limit

- Solicitar: `scope="ticketera_solicitar_reset"`, `limit=5`, `window_seconds=900`, identidad `f"{ip}:{identity_lower}"`.
- Confirmar (solo B): `scope="ticketera_confirmar_reset"`, `limit=10`, `window_seconds=900`, identidad `ip`.

#### Errores y códigos (resumen)

| Status | Cuándo | Body |
|---|---|---|
| 200 | Siempre que el payload sea válido y no se supere RL | `{"detail": "..."}` |
| 400 | Falta XOR (ambos o ninguno) | shape DRF |
| 429 | Rate limit | `{"error": "too_many_attempts", ...}` |
| 503 | Integración off | `{"error": "integration_disabled", ...}` |

---

## 4. Archivos a tocar

> Lista exhaustiva. Cada item indica motivo. **Ningún cambio** rompe los tres endpoints actuales.

- [ticketera/api_views.py](../../ticketera/api_views.py) — agrega `TicketeraUsuarioUpdateView` y `TicketeraSolicitarResetPasswordView` (y `TicketeraConfirmarResetPasswordView` si va Opción B). Reusa `_is_ticketera_source`, `_ticketera_disabled_response`, `AUDIT_SOURCE`.
- [ticketera/api_serializers.py](../../ticketera/api_serializers.py) — agrega `TicketeraUsuarioPatchSerializer`, `TicketeraUsuarioDetailSerializer`, `TicketeraSolicitarResetSerializer` (y `TicketeraConfirmarResetSerializer` en Opción B). Mantener el `pylint: disable=abstract-method` del módulo.
- [ticketera/api_urls.py](../../ticketera/api_urls.py) — agrega `path("usuarios/<str:username>/", TicketeraUsuarioUpdateView.as_view(), name="ticketera-usuarios-detail")` y `path("auth/solicitar-reset-password/", ...)`. (Opción B suma `auth/confirmar-reset-password/`).
- [tests/test_ticketera.py](../../tests/test_ticketera.py) — agrega bloques PATCH y reset (ver sección 5).
- [ticketera/tests.py](../../ticketera/tests.py) — agrega smoke tests del 503 con flag deshabilitado para los endpoints nuevos (mantener cobertura paritaria con los actuales).
- [docs/registro/decisiones/2026-06-08-ticketera-edit-usuarios-y-reset-password.md](../registro/decisiones/2026-06-08-ticketera-edit-usuarios-y-reset-password.md) **nueva** — ADR con las decisiones de la sección 2.
- [docs/registro/cambios/2026-06-08-ticketera-edit-usuarios-y-reset-password.md](../registro/cambios/2026-06-08-ticketera-edit-usuarios-y-reset-password.md) **nueva** — registro de cambio del PR.

**No** se tocan:
- `users/services_auth.py` (Opción A reusa sin modificar; Opción B también).
- `users/models.py`, `users/migrations/` (no hay nuevos campos).
- `core/api_auth.py`, `users/rate_limits.py`, `audittrail/context.py` (reusados sin modificar).
- `config/settings.py` (`TICKETERA_ENABLED` ya existe).

---

## 5. Tests nuevos

Todos en [tests/test_ticketera.py](../../tests/test_ticketera.py) salvo los smoke que van en [ticketera/tests.py](../../ticketera/tests.py).

### PATCH `/usuarios/<username>/`

1. `test_patch_usuario_actualiza_email_y_nombres_devuelve_200` — happy path; verifica que `auditlog` registró un UPDATE con `source=ticketera`.
2. `test_patch_usuario_otro_origen_devuelve_403` — usuario con `source=sisoc` → 403 `user_not_ticketera`, sin modificar.
3. `test_patch_usuario_inexistente_devuelve_404` — username que no existe → 404, sin LogEntry.
4. `test_patch_usuario_acepta_variantes_de_capitalizacion` — `username__iexact` resuelve `Juan.Perez` cuando la fila es `juan.perez`.
5. `test_patch_usuario_email_invalido_devuelve_400` — payload `{"email": "no-es"}` → 400 sin tocar la fila.
6. `test_patch_usuario_idempotente_no_emite_logentry` — mandar los mismos valores actuales → 200 y `auditlog` no suma entradas.
7. `test_patch_usuario_intento_username_o_password_ignorado` — `{"username": "otro", "password": "x"}` no cambia nada y responde 200 con el snapshot actual (DRF ignora fields no declarados).
8. `test_patch_usuario_source_no_se_persiste_en_profile` — mandar `"source": "ticketera-qa"` no escribe en `profile.source` (solo a `extra.remote_source`).
9. `test_patch_usuario_503_con_flag_deshabilitado` (smoke en `ticketera/tests.py`).
10. `test_patch_usuario_sin_api_key_rechaza` — parametrizar con el resto.

### POST `/auth/solicitar-reset-password/`

11. `test_solicitar_reset_con_username_existente_ticketera_devuelve_200_y_envia_mail` — verifica que `send_password_reset_link` fue invocado (mock); LogEntry ACCESS con `source=ticketera`.
12. `test_solicitar_reset_con_email_existente_ticketera_devuelve_200_y_envia_mail` — idem por email.
13. `test_solicitar_reset_usuario_inexistente_devuelve_200_sin_enviar_mail` — anti-enumeration; mock de send no se llama; sin LogEntry.
14. `test_solicitar_reset_usuario_de_otro_origen_devuelve_200_sin_enviar_mail` — `source=sisoc`; anti-enumeration; mock de send no se llama; sin LogEntry.
15. `test_solicitar_reset_usuario_inactivo_devuelve_200_sin_enviar_mail` — `is_active=False`; mock de send no se llama.
16. `test_solicitar_reset_payload_invalido_devuelve_400` — ni username ni email → 400; ambos → 400.
17. `test_solicitar_reset_supera_rate_limit_devuelve_429_en_el_intento_6` — 5 ok, el 6° bloqueado (limit=5, window=900).
18. `test_solicitar_reset_503_con_flag_deshabilitado` (smoke en `ticketera/tests.py`).
19. `test_solicitar_reset_sin_api_key_rechaza` — parametrizar con el resto.

> Si se elige Opción B, sumar:
> 20. `test_confirmar_reset_token_valido_aplica_y_baja_must_change_password`.
> 21. `test_confirmar_reset_token_invalido_devuelve_400`.
> 22. `test_confirmar_reset_password_debil_devuelve_400`.
> 23. `test_confirmar_reset_supera_rate_limit_429`.
> 24. `test_confirmar_reset_503_con_flag_deshabilitado`.

### Cómo correr los tests

`docker run --rm` con la imagen `*-django` ya construida y `USE_SQLITE_FOR_TESTS=1`, igual que el hardening 2026-05-28 (ver sección Validación de [ese cambio](../registro/cambios/2026-05-28-integracion-ticketera-hardening.md)). El Python local sigue con el `ImportError` documentado en la memoria de validación. Limitar a `pytest tests/test_ticketera.py ticketera/tests.py` para mantener tiempo bajo. **No** se requiere migración.

---

## 6. Documentación a actualizar

- **Nueva ADR**: [docs/registro/decisiones/2026-06-08-ticketera-edit-usuarios-y-reset-password.md](../registro/decisiones/2026-06-08-ticketera-edit-usuarios-y-reset-password.md). Contiene:
  - Decisiones de sección 2 con su justificación final.
  - Contratos de los dos endpoints (mismo estilo que el ADR 2026-05-27).
  - Tradeoff Opción A vs B documentado, con la decisión final.
- **Nuevo registro de cambio**: [docs/registro/cambios/2026-06-08-ticketera-edit-usuarios-y-reset-password.md](../registro/cambios/2026-06-08-ticketera-edit-usuarios-y-reset-password.md). Lista archivos tocados, decisiones, impacto y validación corrida.
- Apéndice corto en [docs/registro/decisiones/2026-05-27-integracion-ticketera.md](../registro/decisiones/2026-05-27-integracion-ticketera.md) → sección "Extensiones (2026-06-08)" con un link al nuevo ADR (para que el ADR base siga siendo el índice).

---

## 7. Riesgos y mitigaciones

1. **Mail no llega o llega tarde** — el envío de SISOC es síncrono (`send_mail`, `fail_silently=False`). Si el SMTP está caído, el endpoint responde 200 igual (anti-enumeration), pero el mail falla. Mitigación: el `except Exception` que ya tiene `request_password_reset_for_email` loguea con `logger.exception`; pedir a Infra que vigile el log; documentar que **no** hay retry automático y que la Ticketera puede reintentar (cubre el caso vía rate limit).
2. **Token de password reset Django expirado mientras el mail no llega** — `PASSWORD_RESET_TIMEOUT` controla la TTL. Verificar el valor configurado en `config/settings.py` antes del merge (si está en default 3 días, alcanza; si está reducido, ajustar). Mitigación: documentar en el ADR el valor efectivo.
3. **PATCH idempotente que se transforma en update sin cambios** — si la lógica no compara `getattr` actual vs nuevo, podríamos disparar `save()` y generar `LogEntry` UPDATE espurio en cada PATCH. Mitigación: comparar campo a campo antes de poblar `update_fields`; test 6 cubre la regresión.
4. **403 vs 404 trade-off en PATCH** — la Ticketera con su API Key puede enumerar usernames SISOC (4xx distinto entre "no existe" y "no Ticketera"). Mitigación: documentar en el ADR; rotar la API Key si hay sospecha de leak; si el equipo de seguridad pide cerrar el canal, switch a 404 unificado es trivial (un branch).
5. **Email duplicado en SISOC** — un reset por email matchea N usuarios; hoy `request_password_reset_for_email` itera todos y envía a cada uno. Si el universo es chico (gobiernos provinciales), es ruidoso pero seguro. Mitigación: documentar el comportamiento; si en el futuro hace falta, restringir a `order_by("id").first()` solo dentro del canal Ticketera.
6. **Filtración del `source` informativo en logs** — el body del PATCH/solicitar acepta cualquier string en `source`. El `audit_context` lo guarda en `extra`. Mitigación: validar `max_length=50` (ya está en los serializers actuales), evitar loggear el cuerpo crudo.
7. **Rate limit insuficiente en `/solicitar-reset/`** — 5/15 min puede ser laxo si la Ticketera fanea solicitudes desde una sola IP. Mitigación: monitorear; el `f"{ip}:{identity}"` previene rotación de identidades desde la misma IP.

---

## 8. Checklist de verificación previa al merge

- [ ] Decisiones de sección 2 confirmadas por el humano (D1-D13).
- [ ] PR apunta a `development` (`--base development`).
- [ ] Los tres endpoints actuales pasan sin cambios (regresión: `tests/test_ticketera.py` original y `ticketera/tests.py` original).
- [ ] Tests nuevos (sección 5) pasan en Docker con `USE_SQLITE_FOR_TESTS=1`.
- [ ] `drf-spectacular` schema check sin warnings (`@extend_schema` cubre todos los responses).
- [ ] `black --check ticketera/`.
- [ ] `pylint` sobre `ticketera/api_views.py`, `ticketera/api_serializers.py`, `ticketera/api_urls.py` (Docker, mismo workaround del hardening).
- [ ] ADR nueva y registro de cambio escritos antes del último commit.
- [ ] El ADR 2026-05-27 referencia el nuevo bloque "Extensiones (2026-06-08)".
- [ ] `makemigrations --check --dry-run` corre limpio (no hay nuevas migraciones esperadas).
- [ ] El changelog automático ([scripts/ci/pr_doc_automation.py](../../scripts/ci/pr_doc_automation.py)) tomó el cambio en el PR doc.
- [ ] Verificación manual con `curl`/Postman documentada en el PR description: PATCH happy path + 200 anti-enumeration del solicitar-reset.

---

## Apéndice — Referencias rápidas

- `_is_ticketera_source`: [ticketera/api_views.py:42](../../ticketera/api_views.py).
- `_ticketera_disabled_response`: [ticketera/api_views.py:52](../../ticketera/api_views.py).
- `audit_context`: [audittrail/context.py:42](../../audittrail/context.py).
- `hit_rate_limit`: [users/rate_limits.py:4](../../users/rate_limits.py).
- `HasAPIKey`: [core/api_auth.py:3](../../core/api_auth.py).
- `request_password_reset_for_email`: [users/services_auth.py:73](../../users/services_auth.py).
- `confirm_password_reset`: [users/services_auth.py:119](../../users/services_auth.py).
- `PasswordResetRequestViewSet` (referencia de patrón): [users/api_views.py:199](../../users/api_views.py).
- `PasswordResetRequestSerializer` (XOR username/email): [users/api_serializers.py:134](../../users/api_serializers.py).
- Campos excluidos del diff de Usuario en auditlog: [audittrail/constants.py:107-112](../../audittrail/constants.py) (`password` fijo, `last_login` opcional). `email`, `first_name`, `last_name` **no** excluidos.
- `Profile.source`: [users/models.py:122](../../users/models.py).
- Tests existentes a respetar: [tests/test_ticketera.py](../../tests/test_ticketera.py), [ticketera/tests.py](../../ticketera/tests.py).
