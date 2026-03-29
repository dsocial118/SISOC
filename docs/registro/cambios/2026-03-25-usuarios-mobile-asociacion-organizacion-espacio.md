## Cambio

Se actualizo el alta y la edicion de usuarios web para soportar el nuevo esquema de acceso a SISOC - Mobile por organizacion o por espacio.

## Implementacion

- Se extendio `users.AccesoComedorPWA` con `tipo_asociacion` y `organizacion`.
- El checkbox de acceso mobile mantiene su lugar en el formulario, pero ahora habilita:
  - tipo de asociacion mobile,
  - seleccion multiple de organizaciones,
  - seleccion multiple de espacios.
- El formulario ahora permite asociaciones mixtas:
  - organizaciones con sus espacios visibles,
  - espacios directos adicionales fuera de esas organizaciones.
- Los espacios seleccionados dentro de organizaciones marcadas se persisten como acceso por organizacion.
- Los espacios seleccionados fuera de las organizaciones marcadas se persisten como acceso directo por espacio.
- Se reemplazaron los selectores visibles de Organizaciones y Espacios por tablas con checks, buscador y scroll, manteniendo sincronizados los campos reales del formulario para conservar validaciones y persistencia existentes.
- Se mantuvo el modelo de alcance final por espacio en la API PWA para no romper contratos actuales.
- Los usuarios mobile creados desde web pasan a tener contraseña inicial generada automaticamente y `must_change_password=True`.

## Impacto

- Un usuario mobile puede quedar asociado a multiples organizaciones o a multiples espacios.
- No puede quedar asociado simultaneamente por organizacion y por espacio.
- Si un espacio deja de pertenecer a una organizacion usada como asociacion mobile, deja de ser visible automaticamente.
- El login web sigue bloqueado para usuarios con acceso mobile activo.

## Validacion

- `docker-compose exec django pytest tests/test_users_pwa_forms.py tests/test_users_services_pwa.py tests/test_users_auth_flows.py tests/test_users_api_login.py tests/test_pwa_comedores_api.py -q`
- `docker-compose exec django python manage.py makemigrations --check users organizaciones comedores`
