# 2026-05-28 - Endurecimiento de endpoints Ticketera

## Contexto

- Endpoints server-to-server de la integración con la Ticketera
  (`integracion/api_views.py`), protegidos por API Key. Arquitectura y contratos
  en
  [docs/registro/decisiones/2026-05-27-integracion-ticketera.md](../decisiones/2026-05-27-integracion-ticketera.md).
- Se detectaron cuatro problemas de robustez/seguridad en `usuarios/` y
  `auth/verificar/`. Las correcciones **no cambian los contratos existentes**
  (`200`/`201`/`401`/`409`/`429` conservan su shape).

## Cambios aplicados

- **Alta sin `500` ante carrera (`TicketeraUsuarioCreateView`).** El bloque
  `create_user` + `Profile` se envuelve en `try/except IntegrityError` (patrón
  de `users/services_pwa.create_operador_for_comedor`). Ante una colisión de
  username por requests concurrentes, se re-consulta y se responde con la misma
  lógica idempotente: `200` si el ganador tiene `source="ticketera"`, `409` si
  tiene otro origen. La resolución se extrajo a `_existing_user_response()` para
  usar el mismo criterio en el pre-chequeo y en el post-`IntegrityError`.
- **Chequeo de existencia case-insensitive.** El lookup pasa de `username=` a
  `username__iexact=`, de modo que `"Juan.Perez"` y `"juan.perez"` no esquivan ni
  la idempotencia ni el `409`. **El username se guarda tal cual se recibe** (no
  se normaliza) para no romper `authenticate()`, que usa el backend default
  (case-sensitive en username) en `verificar`.
- **Validación de fortaleza de contraseña en el alta.** Antes de crear el
  usuario se ejecuta `password_validation.validate_password` (que usa
  `AUTH_PASSWORD_VALIDATORS`) contra un `User` no persistido con
  username/email/nombre. Si la contraseña es débil responde `400` con
  `{ "password": [<mensajes>] }` y no crea nada. Corre en el camino de creación,
  después de resolver idempotencia/conflicto, para no alterar `200`/`409`.
- **Rate limit de `verificar` con IP en la identidad.** `hit_rate_limit` pasa de
  `identity=username` a `identity=f"{ip}:{username}"` con
  `ip = request.META.get("REMOTE_ADDR", "anon")` (mismo patrón que
  `PasswordResetRequestViewSet`). Se mantienen `scope="ticketera_verificar"`,
  `limit=10`, `window_seconds=300`.

## Decisiones

- **No se normaliza el username almacenado.** Solo el chequeo de existencia es
  case-insensitive; persistir el valor original preserva el login
  case-sensitive de `authenticate()`. La unicidad entre variantes de
  capitalización queda cubierta por la collation case-insensitive de MySQL
  (default), que dispara el `IntegrityError` que el alta ahora maneja.
- **No se agrega un contador de rate limit por-IP separado.** El endpoint es
  S2S detrás de API Key y el tráfico legítimo llega desde una IP/proxy
  compartido en nombre de muchos usuarios; un tope por-IP estrangularía logins
  legítimos. El perímetro contra rotación de usernames es la API Key. Detalle y
  alternativa (keyear por identidad de cliente) en el ADR.

## Impacto esperado

- Alta concurrente con el mismo username: nunca `500`; resuelve a `200` o `409`
  según el `source` del ganador.
- Idempotencia y `409` funcionan sin importar mayúsculas/minúsculas.
- Contraseña débil: `400` sin crear usuario.
- El rate limit de `verificar` incorpora la IP a la identidad.
- Sin cambios en los shapes `200`/`201`/`401`/`409`/`429`.

## Validación

- `black --check` sobre `integracion/api_views.py`,
  `integracion/api_serializers.py` e `integracion/tests.py`: **OK**.
- Tests de regresión del endurecimiento en `integracion/tests.py`:
  idempotencia/409 case-insensitive, contraseña débil `400` sin crear, carrera
  `200`/`409` vía `IntegrityError` mockeado e identidad del rate limit con IP.
  Los happy-paths, permisos y auditoría se cubren en
  `tests/test_integracion_ticketera.py`.
- **`pytest`: 24 passed.** El Python local está roto
  (`ImportError: cannot import name 'punycode' from 'django.core.validators'`),
  así que la suite se corrió en un contenedor efímero (`docker run --rm` con la
  imagen `*-django` ya construida, montando el checkout y con
  `USE_SQLITE_FOR_TESTS=1`). Pasaron las 9 de `integracion/tests.py` (flag +
  regresiones del endurecimiento) y las 15 de `tests/test_integracion_ticketera.py`,
  confirmando que los cambios no rompen los happy-paths ni la auditoría.

## Riesgos y rollback

- **Riesgo:** en una collation MySQL case-sensitive (no default), dos altas
  concurrentes con distinta capitalización del mismo username podrían crear dos
  filas distintas (la constraint única no las consideraría duplicadas). Escenario
  fuera de la configuración default; se asume collation case-insensitive.
- **Rollback:** revertir `integracion/api_views.py` a la versión previa al
  endurecimiento (los cambios están acotados a las dos vistas) y quitar
  `integracion/tests.py` si fuese necesario.
