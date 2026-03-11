# Profesionalización de Usuarios/Perfil + Permisos por Grupo

## Diagnóstico

- Entidades:
  - `auth.User`
  - `users.Profile`
  - `auth.Group`
  - `auth.Permission`
- Problema detectado:
  - La capa `Group -> Role (1:1) -> Permission` agregaba complejidad sin aportar valor.
  - El objetivo real es que **los grupos contengan permisos** y los usuarios hereden permisos por pertenencia a grupos.

## Diseño implementado

### Modelo objetivo

```text
User --(M2M)--> Group --(M2M)--> Permission
User --(M2M)--> Permission (opcional, directo)
```

### Decisiones

1. Se adopta el modelo estándar Django para autorización.
2. Los helpers existentes (`group_required`, `has_group`, `user_has_role`) ahora interpretan "rol" como permiso por nombre (compatibilidad semántica).
3. Se mantiene fallback temporal por nombre de grupo para no romper flujos existentes.

## Plan por etapas

### PR1 - Seguridad de contraseña
- `must_change_password`
- `password_changed_at`
- `initial_password_expires_at`
- Middleware de cambio obligatorio.

### PR2 - Reset de contraseña (API + Web UI SISOC)
- Request/confirm por API.
- UI dedicada SISOC para request/done/confirm/complete (templates `user/...`).
- No dependencia del admin para el flujo de usuario final.

### PR3 - Grupos con permisos Django
- UI de grupos para crear/editar y asignar permisos.
- Selector de permisos en formato dual-listbox (patrón del admin Django).
- Bootstrap de permisos legacy por nombre de grupo para compatibilidad.
- Al crear grupos nuevos, se garantiza permiso homónimo para compatibilidad legacy.
- Checks de autorización basados en permisos efectivos por grupo.

### PR4 - Permisos directos por usuario
- UI de usuarios con campo de permisos directos (`user.user_permissions`).
- Asignación persistida junto con grupos en alta/edición de usuarios.

## Migraciones necesarias

- `users/migrations/0013_profile_password_security_fields.py`
- `users/migrations/0014_bootstrap_group_permissions.py`
- `users/migrations/0015_assign_bootstrap_group_permissions.py`

## Endpoints / UI de auth

- `GET/POST /password_reset/` (request)
- `GET /password_reset/done/`
- `GET/POST /reset/<uidb64>/<token>/` (confirm)
- `GET /reset/done/`
- API:
  - `POST /api/users/password-reset/request/`
  - `POST /api/users/password-reset/confirm/`

## Suite de tests agregada/ajustada

Archivo: `tests/test_users_auth_flows.py`

- Email obligatorio en ABM de usuarios.
- Primer ingreso con cambio obligatorio.
- Reset API y reset web.
- Verificación de autorización por permisos de grupo.
- Verificación de formulario de grupos con asignación de permisos Django.

## Operación recomendada post-deploy

1. `python manage.py migrate`
2. `python manage.py sync_group_permissions_from_registry`
