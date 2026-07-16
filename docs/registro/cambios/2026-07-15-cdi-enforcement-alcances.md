# CDI: enforcement de alcances SIMEPI

## Cambio

Las vistas CDI reutilizan un scope central que aplica:

- EGP: scopes territoriales de `ProfileTerritorialScope`.
- Referente: CDIs con `AccesoCDI` activo.
- Trabajador: CDIs vinculados por `Trabajador.usuario`.
- Administrador, Analista, Equipo Nacional y Auditoría: alcance nacional.

El rol Auditoría no puede mutar CDIs, trabajadores, nóminas ni formularios,
incluso si recibiera permisos mutantes por otra vía. Las rutas de trabajadores
ahora verifican los permisos propios de `Trabajador`.

## Validación

`docker compose exec -T django pytest centrodeinfancia/tests/test_access_scope_centrodeinfancia.py centrodeinfancia/tests/test_automatic_user_provisioning.py centrodeinfancia/tests/test_trabajadores_views.py -p no:cacheprovider` (36 passed).
