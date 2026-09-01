# Cambio: rol "Relevador DataCalle" en el alta de usuarios

## Alcance

Primer paso de la integracion de la app DataCalle (relevamiento de personas en
situacion de calle) con SISOC: habilitar el acceso a la aplicacion desde el
alta y la edicion de usuarios del backoffice, sin todavia crear el modulo
`datacalle` ni sus endpoints de datos.

## Comportamiento

- El formulario de usuarios suma la tarjeta "Acceso SISOC - Mobile DataCalle",
  espejo de "Acceso SISOC - Mobile Territorial comedor": un check
  (`Profile.es_relevador_calle`) y un selector de provincias que solo se muestra
  con el check activo.
- Marcar el check exige al menos una provincia; al desmarcarlo se borra el
  alcance provincial guardado.
- El alcance vive en `RelevadorCalleProvincia` (una fila por provincia), tabla
  dedicada al rol, igual que `TerritorialComedorProvincia`.
- `POST /api/users/login/` acepta a estos usuarios: antes solo pasaban el
  representante/operador PWA y el territorial de comedores.
- `GET /api/users/me/` agrega `profile.es_relevador_calle` y
  `profile.datacalle_provincias` (`[{id, nombre}]`). Las provincias se informan
  vacias si el usuario no tiene el flag activo.

## Decisiones

- Rol independiente, no reutiliza `es_coordinador` (que es Coordinador de
  Gestion de duplas) ni `ProfileTerritorialScope` (alcance del backoffice
  provincial), para no acoplar el acceso mobile a permisos web.
- Sin exclusion mutua con los roles de comedores: DataCalle es otra aplicacion,
  por lo que una persona puede relevar comedores y situacion de calle.
- El rol dentro de DataCalle (administrador / coordinador / entrevistador) queda
  pendiente: todavia no esta acordado con el cliente movil.
