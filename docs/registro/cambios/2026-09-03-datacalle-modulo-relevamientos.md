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

## Diseño

Las pantallas usan la paleta de SISOC (superficies azul marino, acento dorado
`#e7ba61`, texto claro) con una hoja propia, `static/custom/css/datacalle.css`,
y reutilizan la tabla y los botones de acción de `listModerno.css`.

- El listado abre con un encabezado de sección y un resumen de operativos por
  estado, y muestra cada fila con el lugar y la duración como dato secundario.
- El estado se lee como chip de color: azul planificado, ámbar en curso, verde
  finalizado.
- El detalle se ordena en tarjetas por tema (dónde, cuándo, equipo,
  observaciones y cierre), con el equipo como fichas con iniciales.
- El formulario agrupa los campos en secciones con ayuda breve en cada una, en
  lugar de una lista plana.
- Los estados vacíos explican qué falta hacer en vez de mostrar campos en blanco.

## Localidades múltiples y cascada (2026-09-03)

- Un operativo puede abarcar **varias localidades o comunas** del mismo
  municipio: `localidad` (FK) pasó a `localidades` (M2M). La migración copia la
  localidad ya cargada antes de borrar la columna, así que no se pierde nada.
- Las localidades elegidas deben pertenecer al municipio seleccionado; lo valida
  el formulario, porque el M2M no existe todavía cuando corre el `clean` del
  modelo.
- La búsqueda del listado incluye el nombre de las localidades.
- **Corrección de la cascada**: no filtraba por dos motivos. Los `change` los
  emite select2 vía jQuery y no ejecutan listeners nativos (`addEventListener`),
  así que ahora se bindea por jQuery cuando existe, igual que
  `centro_create_form.js`; y tras reemplazar las opciones hay que reinicializar
  select2 con `window.refreshSelect2Element`. Mientras espera la respuesta el
  combo muestra "Cargando...".
