# API Ticketera

API server-to-server entre la Ticketera y SISOC. SISOC es la fuente de verdad de credenciales.

## Convenciones

- **Base URL**: `/api/ticketera/`
- **Autenticación**: header `Authorization: Api-Key <key>` en todos los endpoints.
- **`source`**: campo opcional en los bodies; identifica el ambiente que llama (`"ticketera"`, `"ticketera-qa"`, `"ticketera-staging"`, ...). Default: `"ticketera"`. Se usa para auditoría; no afecta la lógica.
- **`503 Service Unavailable`**: cualquier endpoint puede devolverlo cuando la integración está deshabilitada por configuración (`{ "error": "integration_disabled", "message": "..." }`).
- **Sin API Key válida**: `401` o `403`.

---

## `POST /usuarios/`

Crea (o reconcilia, si ya existe) un usuario en SISOC. Idempotente cuando el username ya pertenece a un alta de la Ticketera.

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

`first_name`, `last_name` y `source` son opcionales.

Respuestas:

- `201 Created` — alta nueva:
  `{ "id", "username", "email" }`.
- `200 OK` — usuario ya existía con origen Ticketera (idempotente):
  `{ "id", "username", "email" }` (devuelve el snapshot existente, no se actualizan campos).
- `400 Bad Request` — payload inválido o password débil:
  `{ "password": ["<motivo>", ...] }` o shape DRF estándar.
- `409 Conflict` — el username ya está tomado por otro origen (no Ticketera):
  `{ "error": "username_taken", "message": "..." }`.
- `503 Service Unavailable`.

Notas:

- El chequeo de existencia es case-insensitive (`Juan.Perez` y `juan.perez` se consideran el mismo).
- El usuario queda con `must_change_password=true`: debe fijar la contraseña definitiva con `/auth/cambiar-password/` antes de operar.
- La contraseña temporal expira automáticamente; pasado ese plazo, el usuario debe usar `/auth/solicitar-reset-password/`.

---

## `PATCH /usuarios/<username>/`

Edita parcialmente los datos básicos de un usuario provisionado por la Ticketera. Solo afecta usuarios cuyo origen es Ticketera.

Request:

```json
{
  "email": "nuevo@ejemplo.gob.ar",
  "first_name": "Juan Pablo",
  "last_name": "Pérez",
  "source": "ticketera"
}
```

Todos los campos son opcionales. Fields no listados (`username`, `password`, etc.) se ignoran.

Respuestas:

- `200 OK` — edición aplicada o idempotente (sin cambios reales):
  `{ "id", "username", "email", "first_name", "last_name" }`.
- `400 Bad Request` — payload inválido (p.ej. email malformado).
- `403 Forbidden` — el usuario existe pero no es de origen Ticketera:
  `{ "error": "user_not_ticketera", "message": "..." }`.
- `404 Not Found` — no existe usuario con ese username:
  `{ "error": "user_not_found", "message": "..." }`.
- `503 Service Unavailable`.

Notas:

- El `<username>` del path se resuelve case-insensitive.
- Es idempotente: mandar los mismos valores actuales devuelve `200` sin generar entrada de auditoría.
- `username` y `password` no se aceptan por este endpoint (`password` tiene `/auth/cambiar-password/`; `username` no se edita).

---

## `POST /auth/verificar/`

Verifica las credenciales de un usuario por cuenta de la Ticketera en cada login.

Request:

```json
{
  "username": "juan.perez",
  "password": "ContraseñaIngresada",
  "source": "ticketera"
}
```

Respuestas:

- `200 OK` — credenciales válidas:
  ```json
  {
    "valid": true,
    "must_change_password": false,
    "user": {
      "id": 17,
      "username": "juan.perez",
      "email": "...",
      "first_name": "...",
      "last_name": "..."
    }
  }
  ```
- `401 Unauthorized` — credenciales incorrectas o usuario inactivo:
  `{ "valid": false, "error": "invalid_credentials" }`.
- `429 Too Many Requests` — más de 10 intentos en 5 minutos para la misma IP/username:
  `{ "error": "too_many_attempts", "message": "..." }`.
- `503 Service Unavailable`.

Notas:

- Si `must_change_password` es `true`, la Ticketera debería forzar al usuario a llamar `/auth/cambiar-password/` antes de habilitar el resto de la sesión.
- No se distingue "usuario inexistente" de "contraseña incorrecta" (ambos son `401`).

---

## `POST /auth/cambiar-password/`

Cierra el ciclo de contraseña temporal (o permite cambio voluntario): valida la actual y fija la definitiva.

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

- `200 OK` — contraseña actualizada:
  `{ "changed": true, "must_change_password": false }`.
- `400 Bad Request` — `new_password` no cumple las políticas de seguridad o es igual a la actual:
  `{ "new_password": ["<motivo>", ...] }`.
- `401 Unauthorized` — `current_password` incorrecta o usuario inactivo:
  `{ "error": "invalid_credentials" }`.
- `429 Too Many Requests` — más de 10 intentos en 5 minutos para la misma IP/username.
- `503 Service Unavailable`.

Notas:

- Aplica tanto al primer cambio de la temporal como a cambios voluntarios; en ambos casos deja `must_change_password=false`.
- No bloquea por temporal expirada: si el usuario conoce su contraseña actual, puede fijar una nueva.

---

## `POST /auth/solicitar-reset-password/`

Inicia un reset de contraseña: SISOC envía un mail al usuario con un link para fijar la nueva clave. La Ticketera **no** maneja tokens; el ciclo lo cierra el usuario por la web de SISOC.

Request — exactamente uno de `username` o `email`:

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

Respuestas:

- `200 OK` — siempre que el payload sea válido y no se haya superado el rate limit. La respuesta es **la misma** exista o no el usuario:
  `{ "detail": "Si el usuario existe en el sistema, se registró la solicitud de reseteo." }`
- `400 Bad Request` — faltan ambos identificadores o llegan los dos.
- `429 Too Many Requests` — más de 5 intentos en 15 minutos desde la misma IP/identidad:
  `{ "error": "too_many_attempts", "message": "..." }`.
- `503 Service Unavailable`.

Notas:

- No se devuelve `401`/`404` para no permitir enumeración de usuarios.
- Solo se envía mail si el usuario existe, está activo y es de origen Ticketera. En cualquier otro caso la respuesta es la misma `200`, pero no se envía nada.
- Cuando el usuario completa el link del mail, SISOC limpia automáticamente `must_change_password` y los flags de contraseña temporal.
