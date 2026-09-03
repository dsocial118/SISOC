# Cambio: módulo de relevamientos DataCalle en el backoffice

## Alcance

App Django nueva `datacalle`. Permite planificar desde SISOC los operativos de
relevamiento de personas en situación de calle, que le bajan al entrevistador
como tarea en SISOC - Mobile DataCalle. Cubre la planificación; la API que
consume la app y la carga de casos son pasos siguientes.

## Comportamiento

- Nueva sección "Relevamientos DataCalle" dentro de "Situación de Calle" en el
  menú. La sección ahora se muestra con permiso de dispositivos **o** de
  relevamientos, y cada entrada verifica el suyo.
- ABM completo (listar con búsqueda y filtro por estado, alta, detalle, edición
  y baja) con los permisos estándar `datacalle.*_relevamiento`.
- Un relevamiento tiene denominación, provincia, municipio y localidad
  opcionales, fase (espacio público o dispositivo de alojamiento), el lugar
  según la fase, fechas de inicio y fin —puede durar uno o varios días—,
  formato en papel, equipo y observaciones. Nace `planificado` y pasa a
  `en_curso` con el primer caso.
- **Alcance provincial**: un usuario provincial sólo ve, edita y planifica
  operativos de sus provincias, y arma el equipo únicamente con entrevistadores
  de esas provincias. Sin alcance configurado no ve nada. Un usuario sin
  restricción territorial ve todo el país.
- El equipo es obligatorio y sólo admite usuarios con el rol entrevistador de
  DataCalle de la provincia del operativo.
- La baja es lógica: el operativo deja de verse y queda en la papelera.
- El cierre en campo (fecha, GPS y observación del asentamiento) tiene sus
  campos en el modelo y se muestra en el detalle cuando llega desde la app.

## Decisiones

- `id` UUID: viaja a la app como identificador opaco y convive con los UUID que
  el dispositivo genera para los casos.
- Los desplegables de equipo y dispositivo se acotan por el alcance del usuario
  y no por la provincia elegida en el formulario: para un coordinador ya es el
  padrón de su provincia, así que se evita una cascada. Que el equipo coincida
  con la provincia del operativo lo valida el formulario.
- Municipio y localidad usan los endpoints de cascada que ya expone `core`.
- El alcance se resuelve con `users.territorial_scope`, el mismo mecanismo del
  resto del backoffice, en lugar de una estructura propia.
