# Cambio: rol "Relevador DataCalle" en el alta de usuarios

## Alcance

Primer paso de la integracion de la app DataCalle (relevamiento de personas en
situacion de calle) con SISOC: habilitar el acceso a la aplicacion desde el
alta y la edicion de usuarios del backoffice, sin todavia crear el modulo
`datacalle` ni sus endpoints de datos.

## Comportamiento

- El formulario de usuarios suma la tarjeta "Acceso SISOC - Mobile DataCalle":
  un check (`Profile.es_relevador_calle`), un desplegable de rol
  (`Profile.datacalle_rol`) y un selector de provincias. Rol y provincias se
  muestran solo con el check activo y ambos son obligatorios al guardarlo.
- El unico rol disponible por ahora es "Entrevistador".
- El alcance vive en `RelevadorCalleProvincia` (una fila por provincia), tabla
  dedicada al rol, igual que `TerritorialComedorProvincia`.
- **El relevador es un usuario solo de la app**: no puede ingresar al
  backoffice (`BackofficeAuthenticationForm` lo rechaza con "Este usuario solo
  puede ingresar desde SISOC - Mobile DataCalle") y se guarda con
  `is_staff=False`.
- Por lo mismo es excluyente con los otros roles de SISOC - Mobile: no puede
  ser a la vez representante PWA ni territorial de comedores.
- `POST /api/users/login/` acepta a estos usuarios: antes solo pasaban el
  representante/operador PWA y el territorial de comedores.
- `GET /api/users/me/` agrega `profile.es_relevador_calle`,
  `profile.datacalle_rol` y `profile.datacalle_provincias` (`[{id, nombre}]`).
  Rol y provincias se informan vacios si el usuario no tiene el flag activo.

## Decisiones

- Rol independiente, no reutiliza `es_coordinador` (que es Coordinador de
  Gestion de duplas) ni `ProfileTerritorialScope` (alcance del backoffice
  provincial), para no acoplar el acceso mobile a permisos web.
- El bloqueo del backoffice se hace en el login, como con el representante PWA,
  y no borrando grupos ni permisos: desmarcar el check devuelve al usuario a su
  situacion anterior sin perder datos.
- Coordinador y administrador de DataCalle quedan pendientes hasta definir sus
  reglas de alcance; el desplegable ya esta preparado para sumarlos.
