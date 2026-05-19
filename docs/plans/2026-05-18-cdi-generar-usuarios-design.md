# Diseño — Generar usuario "CDI - Referente centro" desde CDI

Rama: `CreacionUsuariosCDI`
Fecha: 2026-05-18
Estado: alcance acordado con PM; pendiente de aprobación para implementar.

## Objetivo

Que un usuario provincial pueda, desde un CDI, presionar "Generar usuario" y
crear hasta 10 usuarios con grupo fijo "CDI - Referente centro", precargados con
los datos del referente ya cargado en el centro. El diseño debe quedar
reutilizable para que a futuro otras apps (Organización, Comedor) repliquen el
mismo patrón.

## Alcance acordado (confirmado con PM)

1. **Qué genera el botón:** un usuario asociado al centro, con datos precargados
   de los campos del referente del CDI:
   - `nombre_referente` → `User.first_name`
   - `apellido_referente` → `User.last_name`
   - `email_referente` → `User.email`
   - `telefono_referente` → `Profile` (no hay campo nativo en `User`)
   - No reemplaza los campos del referente del CDI: coexisten.
2. **Rol/grupo:** fijo **"CDI - Referente centro"**. En el flujo de generación
   el grupo se autocompleta y NO se puede modificar.
3. **Quién puede usar el botón:** usuario provincial que tenga
   "CDI - Referente centro" entre sus grupos delegables
   (`Profile.grupos_asignables`). Reutiliza el IAM existente; no se programa
   lógica nueva tipo "if es_provincial".
4. **Alcance del provincial:** genera/gestiona usuarios de cualquier CDI de su
   provincia (`provincial.profile.provincia == centro.provincia`).
5. **Cardinalidad y límite:** hasta **10 usuarios por CDI**, todos con grupo
   "CDI - Referente centro" (modelo 1..N). El primero se precarga del referente;
   los siguientes pueden ir en blanco.
6. **Permisos del usuario "CDI - Referente centro":** todo el dominio CDI
   EXCEPTO crear centros (`centrodeinfancia.add_centrodeinfancia`) y eliminar el
   centro (`centrodeinfancia.delete_centrodeinfancia`).
7. **Contraseña:** temporal, visible para el provincial en el ABM (como hoy) y
   además se dispara mail al referente con las credenciales. Ambas.
8. **Alcance del referente logueado:** ve/edita SOLO sus CDIs asociados.
9. **Auditoría:** se suma el modelo de vínculo a la lista canónica de
   `audittrail/constants.py`. El alta queda en `/auditoria/` con el actor
   (provincial) capturado por el middleware. `auth.User` y `CentroDeInfancia`
   ya están auditados.

## Plan de implementación

### 1. Modelo de vínculo — `AccesoCDI`

- Ubicación: `centrodeinfancia/models.py` (el dominio CDI es dueño de la
  relación; evita acoplar `users/` → `centrodeinfancia`).
- Espeja `AccesoComedorPWA` (`users/models.py`) sin lo PWA:
  - `user` (FK User, related_name="accesos_cdi")
  - `centro` (FK CentroDeInfancia, related_name="accesos_usuarios")
  - `creado_por` (FK User, SET_NULL, null/blank)
  - `activo` (BooleanField default=True)
  - `fecha_creacion` (auto_now_add), `fecha_baja` (null/blank)
  - `UniqueConstraint(user, centro)`
  - índices `(centro, activo)`, `(user, activo)`
- El rol lo da el grupo, no un campo del modelo.
- Migración nueva (tabla nueva, sin retrofit de FK → bajo riesgo; distinto al
  caso de pérdida de datos por migración de FKs).

### 2. Service genérico — `users/services_generate_user.py` (nuevo)

`generar_usuario_delegado(*, actor, datos, grupo_nombre, vinculo_callback, limite_check=None)`:

- Valida que `actor` pueda delegar `grupo_nombre` (en
  `actor.profile.grupos_asignables` o `actor.is_superuser`). Reutiliza la lógica
  de `DelegationScopeMixin` (`users/forms.py`).
- Si `limite_check()` es falso → `ValidationError` ("máx 10 alcanzado").
- Crea `User` (`is_staff=True`, web — NO PWA), genera password temporal con
  `generate_temporary_password_for_user` (`users/services_auth.py`), setea
  `Profile` (`must_change_password=True`, `temporary_password_plaintext`,
  `initial_password_expires_at`), asigna el grupo.
- Llama `vinculo_callback(user)` en la misma transacción.
- Manda mail al referente (reusa template `user/bulk_credentials_email.txt`).
- El `vinculo_callback` lo provee la app CDI → el service NO importa
  `centrodeinfancia` y queda reutilizable para Organización/Comedor.

Username: derivado del local-part del email; si vacío o duplicado, sufijo
`-<n>` para garantizar unicidad.

### 3. Flujo en CDI

- Botón "Generar usuario" en el detalle del CDI, visible solo si:
  - el actor puede delegar el grupo, y
  - `actor.profile.provincia == centro.provincia`, y
  - `AccesoCDI.objects.filter(centro=centro, activo=True).count() < 10`.
- `GenerarUsuarioCDIView` + `GenerarUsuarioCDIForm`:
  - sin campo grupo (fijo),
  - precarga `nombre_referente`/`apellido_referente`/`email_referente`/
    `telefono_referente`,
  - POST llama al service con `grupo_nombre="CDI - Referente centro"`,
    `vinculo_callback=lambda u: AccesoCDI.objects.create(user=u, centro=centro, creado_por=request.user)`,
    `limite_check=lambda: count_activos < 10`.
- URL nueva en `centrodeinfancia/urls.py`.

### 4. Grupo bootstrap "CDI - Referente centro"

- Entrada nueva en `LISTADO_DEFINED_GROUPS` (`users/bootstrap/groups_seed.py`)
  con todos los permisos del dominio CDI MENOS
  `centrodeinfancia.add_centrodeinfancia` y
  `centrodeinfancia.delete_centrodeinfancia`.
- Enumerar los `centrodeinfancia.*` + `auth.role_*` relevantes desde el
  registry IAM.
- Se aplica con `sync_group_permissions_from_registry` post-deploy (paso
  operativo ya documentado).

### 5. Scope del referente (punto 8) — paso de mayor riesgo

- Función en `centrodeinfancia/access.py`: si el user tiene `AccesoCDI` activos
  → restringe el queryset a esos centros; si no, cae al filtro provincial
  actual. Integrar en list/detail/edit de `centrodeinfancia/views.py` sin
  romper provincial/superuser.
- Foco de tests acá para no regresionar el acceso existente.

### 6. Auditoría

- Agregar `TrackedModelDefinition` de `AccesoCDI` a
  `get_tracked_model_definitions()` en `audittrail/constants.py`
  (excluir `fecha_creacion`).

### 7. Tests (pytest dentro del contenedor `sisoc_2-django-1` con `docker exec`)

- Service: sin grupo delegable → denegado; fila 11 → rechazada; happy path crea
  User + grupo + AccesoCDI + pass temporal + mail (mock).
- Vista: provincial de otra provincia → bloqueado; visibilidad del botón.
- Scope: referente ve solo sus centros; provincial/superuser sin regresión.

## Riesgos

- **Paso 5 (scope):** no regresionar acceso provincial/superuser. Mitigación:
  tests antes de tocar vistas.
- **Bootstrap de grupo:** requiere correr `sync_group_permissions_from_registry`
  post-deploy (paso operativo ya conocido).
- **Username/email del referente:** el email del referente puede estar vacío o
  duplicado; la estrategia de sufijo lo cubre, pero conviene validarlo en QA.

## Operativa

Se trabaja sobre la branch actual `CreacionUsuariosCDI` (decisión del equipo;
es la branch en uso para el tkt). No se crea worktree dedicado.

## Estado de implementación (2026-05-18)

Implementado y validado en la branch `CreacionUsuariosCDI`:

- Modelo `AccesoCDI` + migración `centrodeinfancia/0029`.
- Service genérico `users/services_generate_user.py`.
- Flujo CDI: `forms_generar_usuario.py`, `views_usuario_cdi.py`, URL
  `centrodeinfancia_generar_usuario`, botón en el detalle (visible según regla).
- Grupo `CDI - Referente centro` en `groups_seed.py` + data migration
  `users/0029` (27 permisos, sin `add/delete_centrodeinfancia`).
- Scope referente en `centrodeinfancia/access.py` aplicado en
  `views.py`, `views_export.py`, `views_formulario_cdi.py`.
- Auditoría: `AccesoCDI` agregado a `audittrail/constants.py`.
- Tests: `centrodeinfancia/tests/test_generar_usuario_cdi.py` (11 casos).
- Precarga: solo el **primer** usuario del CDI se precarga con los datos del
  referente; del segundo en adelante el formulario va en blanco (son personas
  distintas y el email del referente ya quedó usado). Decisión del PM.
- UX post-creación: página de confirmación persistente
  (`usuario_cdi_generado.html`) con la contraseña temporal en campo readonly
  (no toast efímero). La vista devuelve `TemplateResponse`.
- Email en dev sale por consola (`EMAIL_BACKEND` console por defecto); en prod
  SMTP por env var. No es bug del feature.
- Panel en la solapa "Referente" del detalle del CDI: tabla de usuarios del
  centro (`AccesoCDI`) con usuario, nombre, email, estado y contraseña temporal
  (oculta como "Ya cambiada" cuando el usuario la cambió). Visible solo para
  el referente del centro (con `AccesoCDI` activo ahí) o superusuario; el
  provincial NO lo ve. Gate: `access.puede_ver_usuarios_cdi`.

Validación ejecutada en contenedor `sisoc_2-django-1`:

- `pytest` nuevos: 10/10. Regresión scope existente: 8/8.
- `black --check`, `djlint --check`, `makemigrations --check`: OK.
- `pylint` (con plugin django): 9.96/10.

### Desviación respecto del diseño

- **Teléfono del referente:** NO se persiste en `User`/`Profile` (ninguno tiene
  campo nativo y agregarlo duplicaría dato). El teléfono sigue viviendo en
  `CentroDeInfancia.telefono_referente` y es alcanzable vía `AccesoCDI`.
  El formulario de generación solo expone nombre/apellido/email. Si negocio
  pide el teléfono en el usuario, requiere `Profile.telefono` + migración
  (fuera de este MVP).

### Notas operativas

- En tests, `config/settings.py` usa sqlite con `TEST MIGRATE=False`: las data
  migrations no corren; los tests crean el grupo vía fixture.
- Post-deploy real: `migrate` aplica la data migration `users/0029`. Igual
  conviene correr `sync_group_permissions_from_registry` (paso ya documentado).
- El alcance del referente se determina por existencia de `AccesoCDI` (no por
  nombre de grupo), evitando acoplar el scope a strings de grupo.

## Pendiente

- Configurar (vía ABM de usuarios) qué usuarios provinciales tienen
  `CDI - Referente centro` en `grupos_asignables`. Es acción de datos, no de
  código.
