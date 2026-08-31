# Usuarios/Perfil + IAM por permisos de Django

## Objetivo

Documentar la implementación actual del módulo de Usuarios/Perfil y la estrategia IAM para:

- Entender cómo funciona hoy.
- Operarlo en ambientes nuevos (staging/producción).
- Replicar el patrón en nuevas features sin volver a hardcodear grupos.

## Estado implementado

## 1) Modelo de autorización

Se adopta el modelo estándar de Django:

- `User` -> `Group` -> `Permission`
- `User` -> `Permission` (directo, opcional)

No se asignan permisos por lógica de `if grupo == "X"` como mecanismo principal.

Compatibilidad:

- **Runtime canónico**: decorators, filtros y helpers aceptan solo permisos
  `app_label.codename`.
- Los aliases legacy quedaron deprecados para enforcement en runtime.
- Se mantiene mapeo legacy únicamente para sincronizar permisos en grupos bootstrap
  existentes (`sync_group_permissions_from_registry`).

## 2) Componentes clave

### Autorización y helpers

- `core/decorators.py`
  - `permissions_any_required([...])`
  - `permissions_all_required([...])`
- `core/templatetags/custom_filters.py`
  - `has_perm_code`
  - `has_any_perm`
- `iam/services.py`
  - `user_has_permission_code`
  - `user_has_any_permission_codes`
  - `user_has_all_permission_codes`
  - `user_has_role` / `user_has_any_role` solo como wrappers de compatibilidad.

### Registro IAM

- `core/permissions/registry.py`
  - `resolve_permission_codes` (canónico, sin aliases).
  - Mapeos legacy solo para bootstrap de grupos existentes.

### Sincronización de permisos por grupo

- `users/bootstrap/groups_seed.py`
- `users/services_group_permissions.py`
- `users/management/commands/create_groups.py`
- `users/management/commands/sync_group_permissions_from_registry.py`
- `users/signals.py`

### ABM de usuarios y grupos

- `users/forms.py`
  - Email obligatorio.
  - Permisos directos de usuario (`user_permissions`).
  - Grupos con permisos (dual listbox).
- `users/views.py`, `users/views_export.py`, `users/urls.py`
  - Accesos de administración por permisos Django (no solo superuser).

## 3) Seguridad de contraseña y recuperación

### Primer ingreso con cambio obligatorio

- Campos en `Profile`:
  - `must_change_password`
  - `password_changed_at`
  - `initial_password_expires_at`
  - `temporary_password_plaintext`
- Middleware: `users/middleware.py` redirige a `password_change_required`.
- Vistas/forms:
  - `FirstLoginPasswordChangeView`
  - `BackofficeAuthenticationForm`

Reglas actuales para usuarios con acceso PWA creados desde web:

- Si el usuario es nuevo y se crea como PWA desde el ABM web:
  - se genera una contraseña automática;
  - se guarda como contraseña real del usuario;
  - el perfil queda con `must_change_password=True`;
  - la contraseña temporal queda visible en la pantalla de edición del usuario
    mientras no haya sido cambiada.
- Si el usuario ya existía y luego se le habilita acceso PWA:
  - se conserva su contraseña actual;
  - no se genera una nueva contraseña automática;
  - no se muestra contraseña temporal nueva.
- Cuando el usuario cambia o resetea su contraseña:
  - `must_change_password` pasa a `False`;
  - se limpia `temporary_password_plaintext`.

### Recuperación PWA

El reseteo PWA reemplaza el reseteo administrativo con contraseña temporal. La
solicitud API requiere el par `username` + `email`; si identifica a un usuario
PWA activo, envía un enlace de recuperación a la URL pública configurada en
`PWA_BASE_URL`. La respuesta no confirma si la cuenta existe y el endpoint
aplica rate limit por IP e identidad. Ver también
`docs/implementaciones/pwa_backend.md` para el contrato de request/confirmación
y `docs/operacion/integraciones.md` para la configuración por ambiente.

### Mi cuenta y confirmación de datos personales

- La autogestión de datos vive en `/mi-cuenta/`; el usuario solo puede editar
  su propio nombre, apellido, DNI, CUIL, mail y correo institucional.
- `/mi-cuenta/confirmar/` es un gate de confirmación de una sola vez para los
  perfiles históricos activos. DNI y CUIL son obligatorios; el correo
  institucional es opcional. La declaración de confidencialidad se conserva
  solo como dato histórico y ya no se muestra ni se exige desde este formulario.
- `ProfileConfirmationMiddleware` se ejecuta después de
  `FirstLoginPasswordChangeMiddleware`: primero se exige el cambio de
  contraseña, si corresponde, y luego la confirmación de datos. Las rutas API
  están exentas para no bloquear clientes PWA/mobile.
- El servidor valida y guarda con `MiCuentaForm`; el botón deshabilitado en la
  interfaz solo es una ayuda de UX y no reemplaza la validación del formulario.
- `Profile.needs_profile_confirmation` y `datos_confirmados_at` registran el
  estado de la confirmación. Las migraciones también crean perfiles faltantes
  para usuarios activos históricos; los nuevos perfiles conservan el default
  de no requerir confirmación.

### Historial de acceso PWA

- Los accesos mobile del usuario no se borran físicamente al quitar permisos.
- `users.AccesoComedorPWA` conserva:
  - `fecha_creacion`
  - `fecha_baja`
  - `activo`
- Además se registra auditoría de movimientos en `users.AuditAccesoComedorPWA` para:
  - alta;
  - reactivación;
  - baja.
- Al desmarcar acceso mobile en edición, el formulario ignora los valores residuales
  de organizaciones/espacios y aplica la baja lógica sin requerir limpiar esos campos
  manualmente.

### Reset de contraseña (web + API)

- Web:
  - `/password_reset/`
  - `/password_reset/done/`
  - `/reset/<uidb64>/<token>/`
  - `/reset/done/`
- API:
  - `POST /api/users/password-reset/request/`
  - `POST /api/users/password-reset/confirm/`
- Servicios:
  - `users/services_auth.py`
  - `users/rate_limits.py`
- Templates UI SISOC:
  - `users/templates/user/password_reset_*.html`
- El reset web selecciona una única cuenta por `username` exacto y usa el email
  como verificación secundaria sin distinguir mayúsculas/minúsculas. Solo
  envía el enlace si la cuenta está activa y ambos valores coinciden; una
  contraseña inutilizable no bloquea el reset.
- La respuesta de solicitud es genérica tanto para combinaciones válidas como
  inválidas. Un email compartido nunca genera enlaces para varias cuentas, lo
  que evita enumeración y resets ambiguos.

## 4) Migraciones aplicadas

- `users/migrations/0013_profile_password_security_fields.py`
- `users/migrations/0014_bootstrap_group_permissions.py`
- `users/migrations/0015_assign_bootstrap_group_permissions.py`
- `users/migrations/0044_profile_confirmacion_datos.py`
- `users/migrations/0045_profile_correo_institucional_declaracion.py`

## 5) Operación post-deploy

Orden recomendado:

1. `python manage.py migrate`
2. `python manage.py sync_group_permissions_from_registry`

Validaciones mínimas:

- Un usuario con permiso puede ver/entrar al módulo.
- Un usuario sin permiso no ve el ítem de sidebar y recibe `403` por URL directa.
- Reset de contraseña web y API funcionan de punta a punta.
- Para perfiles históricos que aún requieran confirmación, un usuario web
  activo debe ser redirigido a `/mi-cuenta/confirmar/`; completar DNI y CUIL
  debe quitar el bloqueo sin pedir la declaración histórica. Verificar también
  que una llamada `/api/` autenticada no sea redirigida.
- Probar el reset web con usuario y email exactos, email con distinta
  capitalización, email compartido, combinación inválida y contraseña
  inutilizable; todos los casos deben conservar la respuesta genérica.

## Guía para nuevas features

## Regla principal

Toda nueva feature debe depender de **permisos Django** (`app_label.codename`), no de nombres de grupo hardcodeados.

## Paso a paso

1. **Definir permisos**
   - Reusar `view/add/change/delete` del modelo cuando alcance.
   - Si es acción especial, crear permiso explícito en el modelo/migración.

2. **Proteger backend**
   - Vistas Django: `permissions_any_required` / `permissions_all_required`.
   - DRF: `has_perm(...)` o clase de permisos equivalente.

3. **Controlar visibilidad en UI**
   - Sidebar/botones con `has_perm_code` o `has_any_perm`.
   - Evitar `request.user.groups...` para control de acceso.

4. **Compatibilidad de grupos existentes**
   - Agregar grupos y permisos canónicos a la semilla bootstrap declarativa.
   - Si impacta producción, agregar data migration o usar sync command.

5. **Testing mínimo**
   - Caso feliz con permiso.
   - Caso sin permiso (`403`).
   - Visibilidad de UI (si aplica).
   - Verificar que aliases legacy no otorguen acceso en runtime.

## Convención recomendada

- CRUD:
  - `app.view_model`
  - `app.add_model`
  - `app.change_model`
  - `app.delete_model`
- Especiales:
  - `app.<accion>_<recurso>`
  - Evitar nombres ambiguos.

## Checklist rápido (PR)

- [ ] No hay checks de `has_group` / `group_required` en código nuevo.
- [ ] Endpoints y vistas protegidos por permisos Django.
- [ ] Sidebar/menú usa permisos.
- [ ] Grupos bootstrap conservan permisos equivalentes.
- [ ] Tests de permisos agregados.
