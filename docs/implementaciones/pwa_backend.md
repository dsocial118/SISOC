# Implementación PWA en Backend (Django + DRF)

## Objetivo

Documentar el estado actual de la API usada por la PWA, el modelo de acceso por comedor y los contratos principales de autenticación y alcance.

## Resumen de implementación

- Autenticación PWA por token DRF:
  - `POST /api/users/login/`
  - `GET /api/users/me/`
  - `POST /api/users/logout/`
- Contexto de usuario en `/api/users/me/` con bloque `pwa`.
- Alcance por comedor aplicado en endpoints PWA de comedores y nómina:
  - si el usuario tiene accesos PWA activos, solo ve/gestiona esos comedores;
  - si no es PWA, se mantiene el filtrado legacy de backoffice.
- Gestión de usuarios de comedor desde PWA:
  - representantes crean/listan/desactivan operadores por comedor.
- Web/backoffice:
  - usuarios con acceso PWA activo no pueden iniciar sesión web.
  - usuarios web siguen pudiendo usar API con token.

## Modelo de acceso PWA

Modelo: `users.AccesoComedorPWA`

- Campos principales:
  - `user`
  - `comedor`
  - `rol` (`representante` | `operador`)
  - `creado_por`
  - `activo`
  - timestamps
- Restricciones:
  - unicidad por `user + comedor`
  - índices para lookup por usuario/comedor/actor.

Servicios de dominio: `users/services_pwa.py`

- `is_pwa_user(user)`
- `get_accessible_comedor_ids(user)`
- `is_representante(user, comedor_id)`
- `create_operador_for_comedor(...)`
- `list_operadores_for_comedor(comedor_id)`
- `deactivate_operador(...)`
- `get_pwa_context(user)`

## Endpoints PWA activos

### 1) Auth + contexto

- `POST /api/users/login/`
  - body: `username`, `password`
  - response: `token`, `token_type`, `user_id`, `username`
- `GET /api/users/me/`
  - requiere `Authorization: Token <token>`
  - incluye `pwa`:
    - `is_pwa_user`
    - `roles`
    - `comedores_representados`
    - `comedor_operador_id`
- `POST /api/users/logout/`
  - invalida token actual.

### 2) Comedores / perfil de espacio

- `GET /api/comedores/{id}/`

Devuelve datos completos del comedor y relacionados (organización, dupla, imágenes, estado, relevamientos, observaciones, clasificaciones, rendiciones, cambios de programa), condicionado por alcance de usuario.

### 3) Documentos de espacio

- `GET /api/comedores/{id}/documentos/`
  - filtros: `tipo`, `q`, `desde`, `hasta`, `page`
  - respuesta paginada: `count`, `num_pages`, `current_page`, `results`
- `GET /api/comedores/{id}/documentos/{documento_id}/download/`

Fuentes de documentos consolidadas: foto legajo, imágenes de comedor, documentación de intervenciones, documentos de rendición final y adjuntos de rendición mensual.

### 4) Nómina

- `GET /api/comedores/{id}/nomina/`
- `POST /api/comedores/{id}/nomina/`
- `PATCH /api/comedores/nomina/{nomina_id}/`

### 5) Prestación alimentaria

- `GET /api/comedores/{id}/prestacion-alimentaria/`
- `GET /api/comedores/{id}/prestacion-alimentaria/historial/`
  - filtros: `desde`, `hasta`, `page`

Se exponen campos de aprobadas del informe técnico (`aprobadas_*`), tomando informes con `estado_formulario="finalizado"`.

### 6) Rendiciones

- `GET /api/comedores/{id}/rendiciones/`
  - filtros: `anio`, `mes`, `desde`, `hasta`, `page`
- `GET /api/comedores/{id}/rendiciones/{rendicion_id}/`
- `POST /api/comedores/{id}/rendiciones/{rendicion_id}/comprobantes/`
  - multipart con `archivo` y opcional `nombre`
- `POST /api/comedores/{id}/rendiciones/{rendicion_id}/presentar/`

### 7) Gestión PWA de usuarios por comedor (representante)

- `GET /api/comedores/{id}/usuarios/`
- `POST /api/comedores/{id}/usuarios/`
  - body: `username`, `email`, `password`
- `PATCH /api/comedores/{id}/usuarios/{user_id}/desactivar/`

## Reglas de permisos y alcance

- `TokenAuthentication` + `IsAuthenticated` en API PWA.
- Scope por comedor:
  - usuarios PWA: `AccesoComedorPWA.activo=True`.
  - usuarios no PWA: filtros existentes de `ComedorService`.
- Gestión de `/usuarios/` protegida con `IsPWARepresentativeForComedor`.
- Usuarios PWA bloqueados en login web por `BackofficeAuthenticationForm`.

## Tests automatizados relevantes

- `tests/test_users_api_login.py`
- `tests/test_users_services_pwa.py`
- `tests/test_users_pwa_forms.py`
- `tests/test_pwa_comedores_api.py`

Cobertura actual incluye auth, contexto, scope por comedor, gestión de operadores, nómina, rendiciones, documentos y prestación.

## Notas operativas

- Para ejecución estable de tests API en contenedor local:
  - usar `DJANGO_DEBUG=False` para evitar interferencias de debug toolbar/silk.
- Smoke manual Postman:
  - colección `postman/PWA Smoke.postman_collection.json`
  - environment `postman/PWA Smoke.postman_environment.json`
  - runner `scripts/run_pwa_smoke_postman.sh`
