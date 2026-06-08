# 2026-06-08 - Ticketera: edición de usuarios y solicitud de reset de contraseña

## Contexto

Extensión aditiva de la API server-to-server con la Ticketera
([ticketera/api_views.py](../../../ticketera/api_views.py)). Se agregan dos
endpoints sin tocar los tres existentes:

- `PATCH /api/ticketera/usuarios/<username>/` — edita `email`, `first_name`,
  `last_name` de un usuario provisionado por la Ticketera.
- `POST /api/ticketera/auth/solicitar-reset-password/` — inicia el reset de
  contraseña; SISOC envía el mail con link a `password_reset_confirm`.

Arquitectura, decisiones y contratos:
[docs/registro/decisiones/2026-06-08-ticketera-edit-usuarios-y-reset-password.md](../decisiones/2026-06-08-ticketera-edit-usuarios-y-reset-password.md).
Plan original (con tradeoffs): [docs/plans/2026-06-08-ticketera-edit-usuarios-y-reset-password.md](../../plans/2026-06-08-ticketera-edit-usuarios-y-reset-password.md).

## Cambios aplicados

- **PATCH `/usuarios/<username>/` (`TicketeraUsuarioUpdateView`).**
  - Solo edita si `_is_ticketera_source(profile.source)` ([ticketera/api_views.py:42](../../../ticketera/api_views.py)); responde `403 user_not_ticketera` en caso contrario, `404 user_not_found` si no existe.
  - Lookup case-insensitive (`username__iexact`); el username almacenado no
    se normaliza.
  - Idempotente: solo persiste los fields que cambian (`update_fields=[...]`);
    PATCH con body vacío o con valores iguales a los actuales responde `200`
    sin tocar nada y sin generar `LogEntry`.
  - Auditoría delegada a `auditlog` sobre `auth_user` (diff automático de
    los tres campos editables; `password` y `last_login` son los únicos
    excluidos del modelo Usuario).
  - Sin rate limit en el MVP.
- **POST `/auth/solicitar-reset-password/` (`TicketeraSolicitarResetPasswordView`).**
  - XOR `username`/`email` (mismo patrón que `PasswordResetRequestSerializer`).
  - Filtro de origen: procesa el reset solo si el usuario activo tiene
    `_is_ticketera_source(profile.source)`. Anti-enumeration: respuesta
    `200` con detalle genérico siempre (existe, no existe, otro origen,
    inactivo, sin email).
  - Dispara `users.services_auth.request_password_reset_for_email` ([users/services_auth.py:73](../../../users/services_auth.py)) — el cierre del ciclo lo
    hace `confirm_password_reset` cuando el portador entra al link.
  - Rate limit `scope="ticketera_solicitar_reset"`, `limit=5`,
    `window_seconds=900`, identidad `f"{ip}:{identity_lower}"`.
  - Emite `LogEntry.ACCESS` explícito sobre el `User` con
    `changes={"password_reset_requested": [None, <isoformat>]}` y
    `audittrail_source="ticketera"`.
- **Serializers nuevos** ([ticketera/api_serializers.py](../../../ticketera/api_serializers.py)):
  `TicketeraUsuarioPatchSerializer`, `TicketeraUsuarioDetailSerializer`,
  `TicketeraSolicitarResetSerializer`, `TicketeraSolicitarResetResponseSerializer`.
- **URLs** ([ticketera/api_urls.py](../../../ticketera/api_urls.py)): suman los
  paths nuevos con names `ticketera-usuarios-detail` y
  `ticketera-auth-solicitar-reset-password`.

## Decisiones

Resumidas — ver el ADR para justificación completa.

- **PATCH editable solo a `email`/`first_name`/`last_name`.** `username` y
  `password` quedan fuera (rompen `authenticate()` o tienen canal propio);
  `is_active` y `source` quedan fuera del MVP.
- **`403` (no `404`) cuando el usuario existe con otro origen.** Mantiene
  utilidad operativa frente al riesgo bajo de enumeración detrás de API Key.
- **Email sin validación de unicidad.** Coherente con `auth_user` actual; no
  se introduce divergencia entre canales.
- **Reset = Opción A (link a `password_reset_confirm`).** Mínima superficie y
  reusa el flujo web. La Opción B (uid+token + endpoint de confirmar) queda
  diseñada en el plan como aditivo futuro si la Ticketera necesita UX nativa.
- **Anti-enumeration en el reset.** 200 genérico siempre.

## Impacto esperado

- Contratos de los tres endpoints actuales sin cambios (200/201/400/401/409/429
  conservan su shape).
- Sin migraciones nuevas, sin cambios en settings.
- La Ticketera puede:
  - corregir email/nombre/apellido de los usuarios que provisionó;
  - disparar el reset de contraseña por mail cuando el portador olvida la
    clave o pide regenerarla.

## Validación

- `pytest tests/test_ticketera.py ticketera/tests.py` en Docker con
  `USE_SQLITE_FOR_TESTS=1` (el Python local sigue con el `ImportError` de
  `punycode` documentado en validaciones previas).
- `black --check ticketera/` sobre los tres archivos del módulo.
- `makemigrations --check --dry-run` — sin nuevas migraciones.

## Riesgos y rollback

- **SMTP caído:** el envío es síncrono (`send_mail(fail_silently=False)`);
  el endpoint responde 200 (anti-enumeration) pero el mail falla. Mitigación:
  `request_password_reset_for_email` ya loguea la excepción con
  `logger.exception`; la Ticketera puede reintentar dentro del rate limit.
- **`PASSWORD_RESET_TIMEOUT`:** verificar el valor efectivo en `config/settings.py`
  antes del rollout (default Django: 3 días).
- **Rollback:** revertir el commit del PR. Los cambios están acotados a los
  tres archivos de `ticketera/`, dos archivos nuevos en `docs/registro/` y
  el apéndice del ADR base.
