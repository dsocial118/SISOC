# Implementación PWA en Backend (Django + DRF)

## Objetivo

Documentar el estado actual de la API usada por la PWA, el modelo de acceso mobile y los contratos principales de autenticación y alcance.

## Resumen de implementación

- Autenticación PWA por token DRF:
  - `POST /api/users/login/`
  - `GET /api/users/me/`
  - `POST /api/users/logout/`
- Contexto de usuario en `/api/users/me/` con bloque `pwa`.
- Alcance por espacio aplicado en endpoints PWA de comedores y nómina:
  - si el usuario tiene accesos PWA activos, solo ve/gestiona esos espacios;
  - si no es PWA, se mantiene el filtrado legacy de backoffice.
- Gestión de usuarios de comedor desde PWA:
  - representantes crean/listan/desactivan operadores por comedor.
- Web/backoffice:
  - usuarios con acceso PWA activo no pueden iniciar sesión web.
  - usuarios sin acceso PWA activo no pueden iniciar sesión en API PWA.

## Modelo de acceso PWA

Modelo: `users.AccesoComedorPWA`

La membresía de un usuario mobile a una organización tiene una fuente de
verdad separada: `users.AccesoOrganizacionPWA`. Las filas de
`AccesoComedorPWA` con `tipo_asociacion='organizacion'` son la proyección de
esa membresía sobre los comedores actuales; no deben usarse para inferir que
la organización sigue asignada cuando quedó temporalmente sin comedores.

- Campos principales:
  - `user`
  - `comedor`
  - `organizacion` (nullable; se usa cuando la asociación mobile es por organización)
  - `rol` (`representante` | `operador`)
  - `tipo_asociacion` (`organizacion` | `espacio`)
  - `creado_por`
  - `activo`
  - timestamps
- Restricciones:
  - unicidad por `user + comedor`
  - índices para lookup por usuario/comedor/actor.

### Asociación mobile de usuarios creada desde Web

- El checkbox de acceso mobile sigue existiendo en el ABM web de usuarios.
- Al marcarlo, el formulario obliga a definir el tipo de asociación:
  - `organizacion`: selecciona una o más organizaciones y luego los espacios visibles dentro de esas organizaciones.
  - `espacio`: selecciona directamente uno o más espacios.
- Regla de negocio: un usuario mobile no puede quedar asociado simultáneamente por organización y por espacio.
- El alta desde Web exige al menos un espacio visible seleccionado. Después del
  alta, una membresía de organización puede quedar sin proyección mientras la
  organización no tenga comedores; la membresía se conserva para que los
  comedores futuros vuelvan a asignarse automáticamente.
- Para usuarios mobile creados desde web:
  - la contraseña inicial se genera automáticamente;
  - el perfil queda marcado con `must_change_password=True`;
  - el acceso web se mantiene bloqueado por `BackofficeAuthenticationForm`.

### Alcance efectivo por organización

- Cuando `tipo_asociacion=organizacion`, el alcance final se resuelve por la
  membresía activa y su proyección de espacios.
- `comedores.signals` captura la organización anterior en `pre_save` y
  reconcilia altas, cambios, baja lógica y restauraciones en `post_save`, dentro
  de la transacción del comedor. Los envíos a GESTIONAR quedan para
  `on_commit`.
- Los cambios hechos con `queryset.update()` o `bulk_create()` no disparan
  señales. Después de una carga de ese tipo debe ejecutarse el comando de
  catch-up; no se debe asumir que la proyección quedó sincronizada.
- La visibilidad final sigue respetando estado/programa mediante
  `filter_pwa_visible_spaces`: asignado no significa necesariamente visible.

#### Catch-up y reconciliación

`python manage.py sincronizar_accesos_pwa_organizaciones` ejecuta un dry-run de
solo lectura. Revisar los totales y luego repetir con `--apply`; se puede
acotar con `--organizacion ID`. El comando procesa cada organización en su
propia transacción y aplica el mismo contrato de totalidad que el formulario:
una organización seleccionada incluye sus comedores actuales y futuros, sin
exclusiones manuales.

Servicios de dominio: `users/services_pwa.py`

- `is_pwa_user(user)`
- `get_accessible_comedor_ids(user)`
- `is_representante(user, comedor_id)`
- `create_operador_for_comedor(...)`
- `list_operadores_for_comedor(comedor_id)`
- `deactivate_operador(...)`
- `get_pwa_context(user)`
- `get_organizacion_ids(user)`
- `sync_organizacion_accesses(organizacion_id=..., comedor_ids=..., actor=...)`
- `apply_comedor_organizacion_change(...)`

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
    - `tipo_asociacion`
    - `organizaciones_ids`
    - `must_change_password`
- `POST /api/users/logout/`
- `POST /api/users/password-reset/request/`
- `POST /api/users/password-reset/confirm/`
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

Para programas cuya nómina se organiza por admisión, todos los flujos PWA usan
exclusivamente la admisión resuelta por
`ComedorService.get_admision_vigente_pwa`: listado, cupos, validaciones,
asistencia y PDF mensual. Si no hay marca `vigente_pwa`, el servicio mantiene
el fallback compatible a la admisión activa de mayor ID y luego a la admisión
de mayor ID. Los programas de nómina directa consultan solo registros del
comedor con `admision_id` nulo; no mezclan registros de admisiones históricas.

### Recuperación de contraseña PWA

- `POST /api/users/password-reset/request/` requiere `username` y `email`.
  Responde de manera genérica y limita intentos por IP e identidad para no
  revelar cuentas.
- Solo se envía el enlace cuando ambos datos corresponden a un usuario PWA
  activo. El enlace apunta a
  `<PWA_BASE_URL>/password-reset-confirm?uid=...&token=...`.
- `POST /api/users/password-reset/confirm/` recibe `uid`, `token` y
  `new_password`; un reset exitoso elimina el requisito de cambiar la
  contraseña inicial.

`PWA_BASE_URL` debe configurarse con la URL pública de Mobile en cada ambiente.
No se debe depender del `Origin` recibido en producción para construir enlaces
de recuperación.

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

### 8) Colaboradores del espacio (representante)

- `GET /api/pwa/espacios/{comedor_id}/colaboradores/`
- `POST /api/pwa/espacios/{comedor_id}/colaboradores/`
- `GET /api/pwa/espacios/{comedor_id}/colaboradores/generos/`
- `GET /api/pwa/espacios/{comedor_id}/colaboradores/actividades/`
- `POST /api/pwa/espacios/{comedor_id}/colaboradores/preview-dni/`
- `PATCH /api/pwa/espacios/{comedor_id}/colaboradores/{id}/`
- `DELETE /api/pwa/espacios/{comedor_id}/colaboradores/{id}/`

Reglas:
- usa la misma fuente de verdad que web/backoffice: `comedores.ColaboradorEspacio`
- el alta sigue la misma regla que en web:
  - primero busca por DNI en ciudadanos SISOC;
  - si no existe, consulta RENAPER;
  - si RENAPER responde correctamente, crea/recupera el `Ciudadano` y luego crea el colaborador del espacio;
- `preview-dni` devuelve el prefill de SISOC/RENAPER antes de guardar;
- `generos` expone el catálogo cerrado de género del colaborador del espacio;
- `actividades` expone el catálogo cerrado de actividades múltiples del colaborador del espacio;
- baja lógica en `DELETE` completando `fecha_baja` sin borrar el registro;
- no se permite duplicar un colaborador activo del mismo ciudadano dentro del mismo espacio;
- se conservan históricos, por lo que la API lista registros activos e inactivos.

### 9) Mensajes del espacio (comunicados a comedores)

- `GET /api/pwa/espacios/{comedor_id}/mensajes/`
- `GET /api/pwa/espacios/{comedor_id}/mensajes/{mensaje_id}/`
- `PATCH /api/pwa/espacios/{comedor_id}/mensajes/{mensaje_id}/marcar-visto/`

Fuente:
- los mensajes PWA se nutren de `comunicados.Comunicado`
- se exponen solo comunicados `externo + comedores + publicado`
- se incluyen comunicados dirigidos al comedor y los marcados para todos los comedores
- no se exponen comunicados vencidos

Lectura y auditoria:
- el estado de lectura se persiste en `pwa.LecturaMensajePWA`
- se registra `visto` y `fecha_visto` por `user + comedor + comunicado`
- cada primer marcado como visto genera auditoria en `pwa.AuditoriaOperacionPWA` con entidad `mensaje_lectura`

## Reglas de permisos y alcance

- `TokenAuthentication` + `IsAuthenticated` en API PWA.
- Scope por espacio:
  - usuarios PWA: `AccesoComedorPWA.activo=True` y, para asociación por
    organización, `AccesoOrganizacionPWA.activo=True`.
  - usuarios no PWA: filtros existentes de `ComedorService`.
- Gestión de `/usuarios/` protegida con `IsPWARepresentativeForComedor`.
- Usuarios PWA bloqueados en login web por `BackofficeAuthenticationForm`.

## Auditoria de operaciones PWA

Modelo: `pwa.AuditoriaOperacionPWA`

- Registra eventos de negocio con:
  - `entidad`, `entidad_id`, `accion`
  - `user`, `comedor`, `fecha_evento`
  - `snapshot_antes`, `snapshot_despues`, `metadata`
- Alcance actual:
- colaboradores: alta/edicion/baja logica
- actividades: alta/edicion/baja logica
- nomina/perfil PWA: alta/edicion/baja logica
- inscripciones de actividad: alta/reactivacion/desactivacion
- lecturas de mensajes/comunicados: marcado de visto por usuario y espacio
- Objetivo:
  - conservar trazabilidad de cambios y estado de registros ante bajas o ediciones.

## Tests automatizados relevantes

- `tests/test_users_api_login.py`
- `tests/test_users_services_pwa.py`
- `tests/test_users_pwa_forms.py`
- `tests/test_pwa_accesos_organizacion.py`
- `tests/test_pwa_comedores_api.py`

Cobertura actual incluye auth, contexto, scope por comedor, gestión de operadores, nómina, rendiciones, documentos y prestación.

## Notas operativas

- Para ejecución estable de tests API en contenedor local:
  - usar `DJANGO_DEBUG=False` para evitar interferencias de debug toolbar/silk.
- Smoke manual Postman:
  - colección `postman/PWA Smoke.postman_collection.json`
  - environment `postman/PWA Smoke.postman_environment.json`
  - runner `scripts/run_pwa_smoke_postman.sh`
- Después de migrar `users.0046` y `users.0047`, ejecutar el dry-run del
  comando de reconciliación y conservar su salida antes de aplicar cambios.


