# Decisión: Ticketera — edición de usuarios y solicitud de reset de contraseña

**Fecha:** 2026-06-08
**Extiende:** [2026-05-27 - Integración SISOC ↔ Ticketera](2026-05-27-integracion-ticketera.md) y el [hardening del 2026-05-28](../cambios/2026-05-28-integracion-ticketera-hardening.md).

---

## Contexto

La integración server-to-server con la Ticketera ya cuenta con tres endpoints:
alta/reconciliación de usuarios, verificación de credenciales y cambio de la
temporal por la definitiva. Faltan dos operaciones para cerrar el ciclo de
gestión de cuentas que la Ticketera necesita:

1. **Editar datos básicos** de un usuario provisionado (email/nombre/apellido),
   por ejemplo cuando el portador corrige su mail o nombre desde el perfil de
   la Ticketera.
2. **Iniciar un reset de contraseña** cuando el portador olvida la clave o pide
   regenerarla, sin atravesar el cambio de la temporal.

Ambas operaciones deben respetar los principios del ADR base: API Key,
HTTP 503 controlado por `TICKETERA_ENABLED`, `audit_context(source="ticketera")`,
rate limit con `users.rate_limits.hit_rate_limit`, y no romper los contratos
existentes de los tres endpoints actuales.

---

## Decisión

Agregar dos endpoints REST nuevos bajo `/api/ticketera/`, protegidos por
`core.api_auth.HasAPIKey` y gated por `settings.TICKETERA_ENABLED`:

| Método | Ruta | Función |
|---|---|---|
| PATCH | `/usuarios/<username>/` | Edita parcialmente `email`/`first_name`/`last_name` del usuario. |
| POST  | `/auth/solicitar-reset-password/` | Dispara el envío del mail de reset (link a `password_reset_confirm`). |

Plan completo (con tradeoffs y decisiones individuales): [docs/plans/2026-06-08-ticketera-edit-usuarios-y-reset-password.md](../../plans/2026-06-08-ticketera-edit-usuarios-y-reset-password.md).

### Patrones reutilizados

- **Permiso:** `HasAPIKey` (canal S2S detrás de API Key, sin Token DRF).
- **Filtro de origen:** `_is_ticketera_source(profile.source)` ([ticketera/api_views.py:42](../../../ticketera/api_views.py)) — alcanza `"ticketera"` y sus variantes por entorno (`"ticketera-qa"`, etc.).
- **Auditoría:** `audit_context(source="ticketera", extra={"remote_source": <source>})`.
- **Rate limit:** `hit_rate_limit` con `identity=f"{ip}:{identidad}"`, mismo patrón que `verificar`/`cambiar-password` y que `PasswordResetRequestViewSet`.
- **Reset por mail:** se reusa `users.services_auth.request_password_reset_for_email` ([users/services_auth.py:73](../../../users/services_auth.py)) sin modificarlo. El cierre del ciclo (validar token + setear nueva clave + limpiar `must_change_password`) lo hace `confirm_password_reset` ([users/services_auth.py:119](../../../users/services_auth.py)) cuando el portador entra al link del mail.

### Sin cambios de modelo

Ninguna migración requerida.

---

## Decisiones explícitas

### Capacidad 1 — PATCH `/usuarios/<username>/`

- **URL con `<username>` como path param.** Es REST estándar, deja un name
  `ticketera-usuarios-detail` y queda mejor documentado por drf-spectacular que
  un PATCH "edit by body" sobre `/usuarios/`. El POST original mantiene el path
  `/usuarios/`.
- **Campos editables:** `email`, `first_name`, `last_name`. No editables por
  este canal:
  - `username` rompe `authenticate()` (ModelBackend case-sensitive) y obliga a
    re-emitir credenciales — fuera de alcance.
  - `password` tiene su propio endpoint `/auth/cambiar-password/` y el reset
    via mail (`/auth/solicitar-reset-password/`); mezclar canales borra
    trazabilidad.
  - `is_active` queda fuera del MVP: introducir desactivación implica decidir
    el flujo de reactivación y la interacción con sesiones web. Se evalúa por
    separado si la Ticketera lo pide.
  - `source` no es editable; se acepta en el body como hint informativo y se
    propaga a `extra.remote_source` para auditoría.
- **Email sin validación de unicidad.** SISOC no impone unicidad de email en
  `auth_user`; sumarla solo en este canal abre divergencia (usuarios SISOC
  existentes podrían ya colisionar y el PATCH no podría reparar el suyo). Si
  la Ticketera necesita unicidad, se discute como cambio aparte.
- **Lookup case-insensitive con `username__iexact`,** mismo criterio que el
  alta. El username almacenado **no** se normaliza.
- **Idempotencia:** solo se persisten los fields que cambian
  (`update_fields=[...]`). Si nada cambia (incluyendo PATCH con body vacío) se
  devuelve `200` con el snapshot actual sin llamar a `save()` y sin generar
  `LogEntry`.
- **403 vs 404 cuando el usuario existe con otro origen:** se mantiene `403
  user_not_ticketera`. El tradeoff (la Ticketera puede enumerar usernames
  SISOC) es chico frente al beneficio operativo (soporte diferencia "no
  existe" de "no te pertenece"). El canal es S2S detrás de API Key, el
  universo enumerable es acotado y la Ticketera ya conoce sus altas. Si
  seguridad pide cerrar el canal, switch a 404 unificado es un branch.
- **Auditoría:** `auditlog` registra el `UPDATE` de `auth_user` con su diff
  automático (los tres campos editables **no** están en `excluded_fields` de
  Usuario — ver [audittrail/constants.py:107-112](../../../audittrail/constants.py): solo `password` y `last_login` están excluidos). No se emite
  `LogEntry` explícito.
- **Sin rate limit en el MVP.** Endpoint baja superficie de riesgo (no toca
  credenciales). Si aparece abuso, agregar `scope="ticketera_editar_usuario"`
  por `f"{ip}:{username}"`.

### Capacidad 2 — POST `/auth/solicitar-reset-password/`

- **Opción A elegida:** el endpoint dispara `request_password_reset_for_email`;
  el mail contiene el link a `password_reset_confirm` y el portador completa la
  nueva clave en SISOC. Pros: mínima superficie nueva, sin tokens fuera de
  SISOC, reusa flujo ya validado. Contras: la UX de cierre vive en SISOC. Si
  la Ticketera necesita UX nativa, se evalúa una Opción B aditiva
  (`uid+token` + `/auth/confirmar-reset-password/`) en otra entrega.
- **Identificación:** `username` o `email`, excluyentes (XOR validado en el
  serializer, mismo patrón que `PasswordResetRequestSerializer`
  ([users/api_serializers.py:134-161](../../../users/api_serializers.py))).
- **Filtro por origen:** solo se procesa el reset si
  `_is_ticketera_source(profile.source)`. La Ticketera no debería operar
  resets sobre usuarios SISOC. La respuesta 200 anti-enumeration cubre el
  filtro silenciosamente.
- **Anti-enumeration absoluta:** respuesta `200` siempre (existe, no existe,
  origen distinto, inactivo, sin email). Mismo texto que la API web actual:
  `"Si el usuario existe en el sistema, se registró la solicitud de reseteo."`
- **Rate limit:** `scope="ticketera_solicitar_reset"`, `limit=5`,
  `window_seconds=900`, identidad `f"{ip}:{username_or_email_lower}"`. Misma
  configuración que el `PasswordResetRequestViewSet` web — el reset es más
  sensible que `verificar`. No se agrega contador por-IP separado (mismo
  motivo documentado en el [hardening 2026-05-28](../cambios/2026-05-28-integracion-ticketera-hardening.md): tráfico legítimo viene de una IP/proxy
  compartido en nombre de muchos usuarios).
- **Auditoría:** cuando el reset se dispara, se emite un `LogEntry.ACCESS`
  explícito sobre el `User` con `changes={"password_reset_requested": [None,
  <isoformat>]}` y `audittrail_source="ticketera"`. El cierre del reset
  (`confirm_password_reset`) seguirá su flujo web (no toca este canal).

### Compatibilidad

- Ningún cambio rompe los tres endpoints actuales (sus shapes `200`/`201`/
  `400`/`401`/`409`/`429` se conservan).
- Sin migraciones nuevas.
- Sin cambios en `users.services_auth` ni en modelos.

---

## Contratos

### PATCH `/api/ticketera/usuarios/<username>/`

Request (todos los campos opcionales):

```json
{
  "email": "nuevo@ejemplo.gob.ar",
  "first_name": "Juan Pablo",
  "last_name": "Pérez",
  "source": "ticketera-qa"
}
```

Respuestas:

- `200 OK` — edición aplicada o idempotente (snapshot):
  ```json
  {"id": 17, "username": "juan.perez", "email": "...", "first_name": "...", "last_name": "..."}
  ```
- `400 Bad Request` — payload inválido (shape DRF; por ejemplo `{"email": ["Enter a valid email address."]}`).
- `403 Forbidden` — `{"error": "user_not_ticketera", "message": "..."}` cuando el username existe con otro origen.
- `404 Not Found` — `{"error": "user_not_found", "message": "..."}` cuando no existe.
- `503 Service Unavailable` — flag deshabilitado.

### POST `/api/ticketera/auth/solicitar-reset-password/`

Request (XOR `username` / `email`):

```json
{ "username": "juan.perez", "source": "ticketera" }
```

o

```json
{ "email": "juan.perez@ejemplo.gob.ar", "source": "ticketera" }
```

Respuestas:

- `200 OK` — siempre que el payload sea válido y no se supere RL:
  `{"detail": "Si el usuario existe en el sistema, se registró la solicitud de reseteo."}`
- `400 Bad Request` — faltan los dos identificadores o llegan los dos
  (shape DRF).
- `429 Too Many Requests` — `{"error": "too_many_attempts", "message": "..."}`.
- `503 Service Unavailable` — flag deshabilitado.

---

## Archivos tocados

- [ticketera/api_serializers.py](../../../ticketera/api_serializers.py) —
  `TicketeraUsuarioPatchSerializer`, `TicketeraUsuarioDetailSerializer`,
  `TicketeraSolicitarResetSerializer`, `TicketeraSolicitarResetResponseSerializer`.
- [ticketera/api_views.py](../../../ticketera/api_views.py) —
  `TicketeraUsuarioUpdateView`, `TicketeraSolicitarResetPasswordView`,
  helper `_user_detail_payload`. Reusa `_is_ticketera_source`,
  `_ticketera_disabled_response`, `AUDIT_SOURCE`.
- [ticketera/api_urls.py](../../../ticketera/api_urls.py) — rutas
  `usuarios/<str:username>/` y `auth/solicitar-reset-password/`.
- [tests/test_ticketera.py](../../../tests/test_ticketera.py) — happy paths,
  403/404, idempotencia, capitalización, anti-enumeration, rate limit,
  auditoría.
- [ticketera/tests.py](../../../ticketera/tests.py) — smoke 503 con flag
  deshabilitado para los dos endpoints nuevos.
- [docs/registro/cambios/2026-06-08-ticketera-edit-usuarios-y-reset-password.md](../cambios/2026-06-08-ticketera-edit-usuarios-y-reset-password.md) — registro de cambio del PR.
- [docs/registro/decisiones/2026-05-27-integracion-ticketera.md](2026-05-27-integracion-ticketera.md) — apéndice "Extensiones (2026-06-08)".

No se tocan: `users/services_auth.py`, `users/models.py`, migraciones, settings.
