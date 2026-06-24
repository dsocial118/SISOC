# Endurecimiento del alcance de administración de usuarios (deny-by-default)

## Fecha
2026-06-24

## Objetivo
Cerrar accesos indebidos en la administración de usuarios: un actor no-superusuario
solo debe ver y operar sobre los usuarios dentro de su alcance delegable
configurado, y nunca sobre superadministradores.

## Alcance
`users/services.py`, `users/forms.py`, `users/views.py` y sus tests.

## Cambios realizados
- **Deny-by-default en `UsuariosService._apply_actor_scope`**: un actor
  no-superusuario que gestiona usuarios pero NO tiene `grupos_asignables` ni
  `roles_asignables` configurados ahora **solo se ve a sí mismo** (antes veía a
  todos los usuarios).
- **Exclusión de superusuarios**: los superadministradores (sin grupos ni roles
  propios) satisfacían trivialmente el filtro de subconjunto; se excluyen para que
  un actor con alcance no los vea ni pueda administrarlos.
- **Cierre de IDOR por URL**: las vistas `UserUpdateView`, `UserDeleteView`,
  `UserActiveView` y `UserGenerateTemporaryPasswordView` ahora restringen su
  queryset al alcance del actor (`get_usuarios_en_alcance`), devolviendo 404 ante
  un `pk` fuera de alcance.
- **Preservación de grupos/roles fuera de alcance** (`CustomUserChangeForm`): al
  editar, el actor ve y conserva los grupos/permisos actuales del usuario aunque
  estén fuera de su alcance; solo puede agregar/quitar dentro de lo que administra.

## Riesgo / Impacto (IMPORTANTE)
Cambio de comportamiento **breaking** para administradores no-superusuario:
- Cualquier admin no-superusuario que dependía de ver/editar a todos los usuarios
  **pierde ese acceso** si no tiene `grupos_asignables`/`roles_asignables`
  configurados en su `Profile`.

## Acción requerida antes de desplegar
1. Verificar en producción qué administradores no-superusuario gestionan usuarios.
2. Configurarles `grupos_asignables`/`roles_asignables` acorde a lo que deben
   administrar; en caso contrario, quedarán limitados a sí mismos por diseño.
3. Confirmar que las cuentas que deben administrar de forma global son
   superusuarios (`is_superuser=True`).

## Rollback
Revertir los cambios en `users/services.py` (volver `return base_qs` en las dos
ramas sin alcance y quitar `.exclude(is_superuser=True)`) restaura el
comportamiento previo. Los `get_queryset` de las vistas pueden mantenerse, ya que
solo refuerzan el control de acceso.
