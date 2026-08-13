# Accesos PWA por organización actualizados automáticamente

Fecha: 2026-08-12

## Qué cambió

Los usuarios mobile asociados a una organización ya no dependen de que un
administrador edite su usuario cada vez que la relación Comedor-Organización
cambia:

- si un comedor se crea dentro de una organización, o pasa a pertenecer a ella,
  se habilita automáticamente en los usuarios asociados a esa organización;
- si un comedor deja de pertenecer a la organización, se da de baja su acceso
  en esos usuarios.

La lógica alcanza únicamente a los accesos con
`tipo_asociacion='organizacion'`. Los accesos por espacio y los operadores
creados desde la PWA no se ven afectados.

La visibilidad final la sigue resolviendo el estado del comedor
(`filter_pwa_visible_spaces`, issue #2084): un comedor recién sumado a la
organización queda asignado, pero no se muestra si su programa/estado no lo
habilita.

## Implementación

- Nuevo modelo `users.AccesoOrganizacionPWA` (usuario + organización + baja
  lógica). Es la fuente de verdad de la relación usuario-organización, que
  antes se deducía de las filas de `AccesoComedorPWA` y se perdía cuando la
  organización se quedaba sin comedores asignados.
- `users.services_pwa`:
  - `sync_representante_accesses` acepta `organizacion_ids` y sincroniza la
    membresía; si no se pasa, la deriva de los `access_specs` (comportamiento
    usado por la importación masiva).
  - `deactivate_representante_accesses` también da de baja las membresías.
  - `apply_comedor_organizacion_change` propaga un cambio de organización de un
    comedor a los usuarios de la organización anterior y de la nueva.
  - `sync_organizacion_accesses` reconcilia una organización completa contra sus
    comedores actuales.
- `comedores.signals` captura la organización previa en `pre_save` y llama al
  servicio de `users` en `post_save`. `users` no importa `comedores`: la
  reconciliación trabaja con IDs primitivos.
- Migraciones `users.0046` (modelo) y `users.0047` (backfill de membresías desde
  los accesos por organización activos).
- Comando `sincronizar_accesos_pwa_organizaciones` (app `comedores`) para el
  catch-up de datos existentes. Corre en dry-run por defecto; con `--apply`
  persiste.

## Impacto y trade-offs

- El comando de catch-up recalcula el alcance completo de cada organización, así
  que repone también los espacios que un administrador haya deseleccionado a
  mano en el alta. La propagación automática, en cambio, es incremental: sólo
  toca el comedor cuya organización cambió y respeta las deselecciones previas.
- Los cambios hechos con `queryset.update()` sobre `Comedor.organizacion` no
  disparan señales y no se propagan; para esos casos correr el comando.
- La baja lógica del comedor (soft delete) sigue sin desactivar accesos PWA;
  es una deuda previa que no cambia con este trabajo.

## Validación

- `docker exec sisoc_2-django-1 pytest tests/test_pwa_accesos_organizacion.py tests/test_users_pwa_forms.py tests/test_users_services_pwa.py tests/test_pwa_comedores_api.py tests/test_users_api_login.py -q`
- `docker exec sisoc_2-django-1 pytest -n auto -q`
- `black .`, `pylint users comedores`, `lint-imports`
