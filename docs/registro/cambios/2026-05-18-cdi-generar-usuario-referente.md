# 2026-05-18 — Generar usuario "CDI - Referente centro" desde CDI

## Qué cambió

Un usuario provincial puede generar, desde el detalle de un CDI, hasta 10
usuarios con grupo fijo `CDI - Referente centro`, precargados con los datos del
referente del centro. El usuario creado queda vinculado al CDI vía `AccesoCDI`
y recibe credenciales temporales (visibles en el ABM y por mail).

## Impacto en permisos / seguridad

- Nuevo grupo bootstrap `CDI - Referente centro`: todos los permisos del
  dominio CDI excepto `centrodeinfancia.add_centrodeinfancia` y
  `centrodeinfancia.delete_centrodeinfancia`.
- Quién puede generar: usuario provincial con `CDI - Referente centro` en
  `Profile.grupos_asignables` (mecanismo IAM existente) y de la misma provincia
  que el CDI. Superusuario sin restricción de provincia.
- Scope del referente: solo ve/edita los CDIs donde tiene `AccesoCDI` activo
  (listado, detalle, edición, export, formularios). Provincial y superusuario
  sin cambios de comportamiento.
- Auditoría: `AccesoCDI` registrado en `audittrail` (el alta queda trazable con
  el actor provincial; actividad posterior del referente ya trazable por los
  modelos CDI auditados).

## Archivos clave

- `centrodeinfancia/models.py` (`AccesoCDI`) + migración `0029`.
- `users/services_generate_user.py` (service genérico reutilizable).
- `centrodeinfancia/views_usuario_cdi.py`, `forms_generar_usuario.py`, `urls.py`.
- `centrodeinfancia/access.py` (scope referente + regla de habilitación).
- `users/bootstrap/groups_seed.py` + `users/migrations/0029`.
- `audittrail/constants.py`, `core/constants.py`.

## Operación post-deploy

1. `python manage.py migrate`.
2. `python manage.py sync_group_permissions_from_registry`.
3. En ABM de usuarios, asignar `CDI - Referente centro` a `grupos_asignables`
   de los usuarios provinciales que deban poder generar.

## Diseño detallado

`docs/plans/2026-05-18-cdi-generar-usuarios-design.md`
