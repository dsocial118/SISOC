# SIMEPI - EGP gestiona referentes de CDI

## Contexto

El detalle de un CDI ocultaba `Usuarios del centro` a los gestores
territoriales, aunque el mismo usuario SIMEPI - EGP podía generar referentes y
editar el CDI dentro de su alcance.

## Cambio

- Un actor que puede delegar `CDI - Referente centro` y tiene alcance sobre el
  CDI puede ver los referentes asociados y usar el alta existente mientras
  haya cupo.
- La edición de nombre, apellido, teléfono y correo del referente continúa en
  el formulario de edición del CDI.
- La visibilidad del panel ya no depende de que quede cupo para nuevas altas.

## Seguridad

La capacidad de gestionar referentes se separó de la capacidad de ver
credenciales. SIMEPI - EGP puede ver usuario, nombre, correo y estado, pero no
recibe contraseñas temporales. El propio referente conserva acceso sólo a su
credencial y el superusuario conserva el acceso administrativo existente.

El queryset territorial del detalle no cambió: un EGP no puede abrir ni editar
un CDI fuera de su alcance.

## Validación focalizada

- Regresión HTTP del detalle: el EGP ve `Usuarios del centro`, el referente y
  `Generar usuario`, sin que la contraseña temporal aparezca en la respuesta.
- Suite focalizada de acceso/generación: 9 pruebas pasaron en dos ejecuciones
  (5 del flujo principal y 4 de límites/compatibilidad).
- Se cubrió edición persistida de los cuatro datos del referente, panel con
  cupo completo y credenciales renderizadas para referente/superusuario.
- `python -m compileall` y `git diff --check` pasaron.
- Black y djLint focalizados pasaron.
