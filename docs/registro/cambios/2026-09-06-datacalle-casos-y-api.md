# Cambio: casos de DataCalle y API para la app

## Alcance

Completa el módulo `datacalle`: además de planificar operativos, SISOC ahora
recibe los casos que carga la app, los muestra, y expone la API con la que la
tarea baja al entrevistador y vuelve el trabajo de campo.

## Comportamiento

- **Casos (encuestas)**: un caso es una persona relevada dentro de un operativo.
  El instrumento se guarda completo como JSON tal como llega, y se copian a
  columnas indexadas los datos que necesitan tableros y filtros.
- **API bajo `/api/datacalle/`**, con token y alcance resuelto por el servidor:
  - `GET /relevamientos/` — las tareas donde el usuario está en el equipo,
    con `?desde=` y `?estado=` para sincronización incremental.
  - `GET /relevamientos/{id}/` y `GET /relevamientos/{id}/encuestas/`.
  - `POST /relevamientos/{id}/cerrar/` — cierre desde la app, con el punto GPS
    y la observación del asentamiento del recorrido. Es idempotente.
  - `PUT /encuestas/{uuid}/` — alta o actualización por UUID del dispositivo:
    reintentar no duplica. `DELETE` da de baja lógica.
  - `GET /catalogos/` — cuestionario y catálogos vigentes.
- **Reglas del servidor**: un operativo finalizado rechaza casos con **409** y
  código `relevamiento_cerrado`; un operativo ajeno responde **404**; con el
  primer caso el operativo pasa a `en_curso`.
- **Backoffice**: el detalle del operativo muestra el resumen de casos y su
  listado, y cada caso tiene su ficha con las respuestas traducidas a
  etiquetas legibles del instrumento.
- **Grupo "Coordinador DataCalle"** en la semilla de grupos, con los permisos
  del módulo y los de gestión de usuarios.

## Decisiones

- **Personas observadas se suman sólo de los casos cabecera de grupo.** El
  módulo observacional se carga una vez por grupo y los demás casos lo heredan,
  así que sumar todos multiplicaría el total.
- **"Sin entrevista" y "menor de edad" se cuentan por separado**: ambos quedan
  como `rechazada`, pero al menor no correspondía preguntarle. Se distinguen
  por la presencia de `realizaEntrevista`.
- **`lat`/`lon` del grupo se extraen server-side** de `respuestas.ubicacionGrupo`
  a columnas propias, descartando el 0,0 y los valores fuera de rango. Así se
  puede mapear sin consultar dentro del JSON y sin pedirle a la app que cambie
  el contrato.
- El instrumento (`datacalle/instrumento/`) es una copia de los artefactos que
  publica la app. Si queda desactualizado, el caso muestra la clave cruda en
  lugar de perder el dato.
- Un caso reenviado después de borrarlo se restaura: la app es la fuente de
  verdad de lo que se relevó en campo.

## Corrección: MySQL "Out of sort memory" en el detalle (2026-09-06)

El detalle de un relevamiento devolvía **500 en producción**, incluso sin casos
cargados: `MySQLdb.OperationalError (1038, 'Out of sort memory')`.

MySQL rechaza un `ORDER BY` cuando **el ancho de una sola fila** no entra en el
`sort_buffer`; decide por el ancho, no por la cantidad de filas, así que fallaba
con la tabla vacía. La consulta de casos ordenaba filas que arrastraban el JSON
del instrumento (`respuestas`, LONGTEXT) más el relevamiento entero por
`select_related`, que suma su propio JSON y dos campos de texto.

- El listado del backoffice usa ahora un queryset con las columnas mínimas.
- El queryset completo dejó de hacer `select_related`: los serializers usan
  `relevamiento_id` y `relevador_id`, que son columnas locales.
- Se agregaron índices `(relevamiento, -fecha_inicio)` y
  `(relevamiento, -updated_at)` en casos, y `(-fecha_inicio, denominacion)` en
  relevamientos, para que el motor resuelva el orden por índice.

**No es reproducible con SQLite**, que no tiene sort buffer: por eso la suite no
lo detectó. Los tests de regresión verifican lo que sí es verificable —que las
consultas queden angostas— en `tests/test_datacalle_repro_500.py`.
