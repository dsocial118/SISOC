# 2026-07-17 - Rol de usuario "Territorial comedor" (SISOC - Mobile)

## Contexto

Primer paso para migrar los territoriales (relevadores) desde identidades que hoy
viven solo en GESTIONAR/AppSheet (`gestionar_uid` + nombre, cacheados por
`TerritorialService`) hacia usuarios reales de SISOC. En esta etapa se agrega
únicamente la marca de rol sobre el `User`; el mapeo con `gestionar_uid` y el
consumo desde la app mobile se resolverán en pasos posteriores.

## Cambio aplicado

- Se agregó el flag `Profile.es_territorial_comedor` (booleano) que marca al
  usuario como territorial de comedores. Es un flag simple: **no** arrastra la
  maquinaria del representante PWA (no auto-genera contraseña, no limpia grupos,
  no oculta el backoffice).
- Se creó el modelo dedicado `TerritorialComedorProvincia` (relación
  `Profile` → `Provincia`, única por par) para el alcance del territorial. El eje
  es la provincia, que es como el pull de territoriales desde AppSheet cachea a
  los relevadores. Se mantiene desacoplado de `ProfileTerritorialScope` (usuarios
  provinciales) y de `AccesoComedorPWA` (representantes PWA).
- En el formulario de usuarios (`UserCreationForm` y `CustomUserChangeForm`, vía
  `TerritorialComedorFormMixin`):
  - nuevo check "Habilitar acceso a SISOC - Mobile" bajo la card
    "Acceso SISOC - Mobile Territorial comedor";
  - multiselect de provincias de alcance;
  - inicialización desde el perfil al editar;
  - guardado del flag y sincronización de las provincias.
- En la UI (`user_form.html`) se muestra el selector de provincias solo cuando el
  check está activo.
- Se habilitó el **login mobile** para territoriales: `POST /api/users/login/`
  antes solo dejaba pasar usuarios con acceso PWA (`AccesoComedorPWA`); ahora
  también acepta usuarios con `Profile.es_territorial_comedor=True`
  (helper `is_territorial_comedor_user` en `users/services_pwa.py`). El resto del
  flujo mobile (`/api/users/me/`, `/logout/`, cambio de contraseña obligatorio)
  ya funciona para cualquier token válido.
- Se agregó el endpoint mobile **`GET /api/territorial/comedores/`** para que el
  territorial lea sus comedores con scope por sus provincias
  (`TerritorialComedorProvincia`). Auth por DRF Token + permiso
  `IsTerritorialComedorUser`. Respuesta paginada (PageNumberPagination) con
  `count/next/previous/results`, más `provincias` (alcance del usuario). Cada
  comedor trae datos básicos (nombre, ubicación, geo, estado) y un resumen de
  relevamientos (`total` + `ultimo`). El scope se resuelve con
  `get_territorial_comedor_provincia_ids`.
- Se agregó **`GET /api/territorial/comedores/{id}/`** (detalle scopeado, 404
  fuera de alcance) y **`POST /api/territorial/comedores/{id}/imagenes/}`**
  (multipart, campo `imagen`, scopeado por provincia, reusa
  `ComedorService.create_imagenes` con `origen="mobile"`, máx 3 fotos/3 MB,
  devuelve URL absoluta).
- Se expuso lo territorial en **`GET /api/users/me/`**: el bloque `profile` ahora
  incluye `es_territorial_comedor` y `territorial_comedor_provincias`
  (`[{id, nombre}]`) vía `get_territorial_comedor_provincias`.
- Contexto: estos endpoints son el contrato para la PWA "SiSOC Mobil" que
  reemplaza a AppSheet/GesCom. Coordinación en el archivo externo
  `COORDINACION-PWA-SISOC.md`.

### Segunda ronda de coordinación PWA (2026-07-17)

- **N4 precarga profunda:** `GET /api/territorial/comedores/{id}/` ahora incluye
  `relevamiento_actual_mobile` (`id/fecha_visita/estado/items/sections`, mismo
  shape que `GET /api/comedores/{id}/` pero scopeado por provincia), reutilizando
  el builder de `ComedorDetailSerializer`.
- **N7 fotos:** límite subido de 3 a **15**; nuevo campo opcional
  `client_uuid` en la subida para **idempotencia** de reintentos offline (dedup
  por `(comedor, client_uuid)`). Requirió `ImagenComedor.client_uuid` +
  `UniqueConstraint` (migración `0048_imagencomedor_client_uuid`).
- **N8 firma:** endpoint dedicado `POST /api/territorial/comedores/{id}/firma/`
  (multipart `firma`, ≤3 MB, scopeado) → devuelve `{url}` para guardar en
  `excepcion.firma` / `cierre.firma_*`. No usa `ImagenComedor` (no contamina la
  galería del comedor).
- **PATCH relevamiento (500→400):** `PATCH /api/relevamiento` sin `sisoc_id` ahora
  responde 400 (antes 500 por KeyError).
- Confirmado (sin cambios): el formato de `fecha_visita` es `d/m/aaaa HH:MM` con
  **barra** (`core/utils.format_fecha_django` usa `"%d/%m/%Y %H:%M"`; acepta
  día/mes sin cero a la izquierda), y el doble `prestacion` (raíz=cupos/`Prestacion`
  vs `espacio.prestacion`=seguridad/higiene/`EspacioPrestacion`) está bien separado.

### Dropdown "Territorial asignado" del backoffice → usuarios SISOC (opción A)

- El desplegable "Territorial asignado" del modal "Nuevo relevamiento" (backoffice)
  dejaba de mostrar territoriales porque leía del **pull viejo de AppSheet**
  (`TerritorialService`), apagado fuera de prod (`GESTIONAR_INTEGRATION_ENABLED`).
- Ahora las vistas `obtener_territoriales_api` / `sincronizar_territoriales_api`
  (`comedores/views_territorial.py`) toman de **usuarios SISOC territoriales
  filtrados por la provincia del comedor** (`get_territorial_comedor_users_for_provincia`
  en `users/services_pwa.py`). Se conserva la forma `{gestionar_uid, nombre}` del
  front; `gestionar_uid` viaja con el **id del usuario** → al crear el relevamiento
  queda en `Relevamiento.territorial_uid` (opción A). Ya no depende de AppSheet.

### Precarga N4: `campo` + `valor` en los items de sections

- Para que la PWA prellene el formulario 1:1, los items de las `sections` basadas
  en el modelo de `relevamiento_actual_mobile` (`GET /api/territorial/comedores/{id}/`
  y `GET /api/comedores/{id}/`) ahora incluyen `campo` (clave snake_case del campo
  del modelo) y `valor` (crudo: bool/número/nombre-de-FK/lista), además de
  `pregunta`/`respuesta`. Cambio en `_collect_model_items` + item de "Observación"
  (`comedores/api_serializers.py`). El `items` resumen y la sección "Información"
  siguen siendo solo display (sin `campo`).

### N3: `relevamientos.items` con todos los relevamientos del comedor

- `GET /api/territorial/comedores/` (lista y detalle) exponía solo
  `relevamientos.ultimo`, elegido por `-fecha_visita, -id`. En MySQL los `NULL`
  van al final en `DESC`, así que un Finalizado con fecha tapaba al pendiente sin
  fecha → el relevamiento pendiente quedaba invisible para la PWA.
- Ahora `relevamientos` incluye `items: [{id, estado, fecha_visita}]` con **todos**
  los relevamientos del comedor (se mantienen `total` y `ultimo` por compat). La
  PWA filtra por estado pendiente para el trabajo por hacer (el modelo garantiza
  ≤1 activo por comedor). Cambio en `TerritorialComedorSerializer.get_relevamientos`
  (`comedores/api_views_territorial.py`).

## Reglas validadas

- **Mutuamente excluyente** con el representante PWA (`es_representante_pwa`): el
  form rechaza tener ambos marcados a la vez, y la UI destilda uno al marcar el
  otro.
- Si el usuario es territorial, debe tener **al menos una provincia** de alcance.
- Si se desmarca el rol territorial, se limpian sus provincias asociadas.

## Archivos

- `users/models.py`
- `users/migrations/0042_profile_territorial_comedor.py`
- `users/forms.py`
- `users/templates/user/user_form.html`
- `users/services_pwa.py`
- `users/api_views.py`
- `users/api_permissions.py`
- `users/api_serializers.py`
- `comedores/api_views_territorial.py`
- `comedores/api_urls_territorial.py`
- `comedores/models.py` (`ImagenComedor.client_uuid`)
- `comedores/migrations/0048_imagencomedor_client_uuid.py`
- `relevamientos/views/api_views.py` (500→400)
- `config/urls.py`

## Validación

- `docker compose exec django python manage.py makemigrations --check`
- `docker compose exec django python manage.py check`
- `docker compose exec django pytest tests/test_users_pwa_forms.py`
- `docker compose exec django pytest tests/test_users_api_login.py`
- `docker compose exec django pytest tests/test_territorial_api.py`
