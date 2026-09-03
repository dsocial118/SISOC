# Celiaquía: comentarios técnicos estructurados y su uso en Subsanar/Rechazar

Fecha: 2026-09-03
Issue: #2318

## Problema

En el detalle del expediente convivían dos registros sin relación entre sí: los
"Comentarios Técnicos" del legajo, que el técnico usaba como anotación interna, y
el motivo que escribía a mano al enviar a subsanar o al rechazar. Como no se
alimentaban entre ellos, el técnico tenía que volver a redactar los motivos que
ya había anotado internamente.

## Cambio

### Comentarios técnicos estructurados

El comentario deja de ser texto libre y pasa a tener tipo de documento
(RENAPER / ANSES / condición diagnóstica), un Sí/No de "¿tiene observaciones?" y,
cuando la respuesta es Sí, una observación de un catálogo por tipo. La opción
"Otros" habilita redacción libre.

Se registran sobre `HistorialComentarios` con el tipo `COMENTARIO_TECNICO`, en
lugar de un modelo propio: el timeline ya aportaba legajo, usuario, fecha,
`estado_relacionado` (estado del legajo al momento del comentario) y `es_interno`
(interno hasta que se publica), que son cinco de los ocho atributos que pedía el
requerimiento. Los campos nuevos son todos nulos, así que las filas existentes y
el resto de los tipos de comentario no se ven afectados.

Cada alta crea un registro nuevo; nada se sobrescribe. El backend valida la
combinación: rechaza un código que no pertenezca al tipo elegido, exige texto con
"Otros", y descarta la observación cuando la respuesta es No.

### Catálogo

Los textos viven como constantes en `celiaquia/comentarios_tecnicos.py`, no como
tabla: son normativos y cambian poco, y una tabla exigiría fixture más data
migration, que además no corre en los tests. Cada comentario guarda el **código**
de la observación y, por separado, el texto renderizado en el campo `comentario`,
que funciona como snapshot histórico: si mañana se reescribe un texto del
catálogo, los comentarios ya emitidos conservan lo que efectivamente se comunicó.

`observacion_codigo` se persiste sin `choices` a propósito. La validez del código
depende del tipo de documento, cosa que un choices plano no puede expresar
(aceptaría un código de RENAPER en un comentario de ANSES). Lo valida el
servicio, y de paso los retoques de redacción del catálogo no generan migraciones.

Al transcribir el catálogo se unificó la puntuación respecto del texto del issue:
`Y /O` → `y/o`, `El/ los` → `El/los`, minúscula después de dos puntos, y punto
final en las que no lo tenían, para que la concatenación no quede con frases
pegadas. Revertirlo es cambiar una constante.

### Visibilidad y publicación

Los comentarios nacen internos. La Provincia recibe únicamente los que tienen
observaciones (Sí), y recién cuando el técnico solicita una subsanación o rechaza
el legajo; los que tienen No quedan internos para siempre. Publicar baja el flag
`es_interno` y sella `publicado_en` / `publicado_por`, que es el registro de
auditoría del evento; los ya publicados conservan la fecha y el usuario original.

A la Provincia se le deduplican las observaciones repetidas: el técnico puede
registrar la misma más de una vez y el historial interno las conserva todas.

El panel de comentarios se le muestra a la Provincia en los estados donde puede
haber algo publicado: `SUBSANAR`, `SUBSANADO`, `RECHAZADO` y `APROBADO`. Queda
afuera `PENDIENTE`. Se enumeran los estados que habilitan el panel, y no los que
lo niegan, para que un estado nuevo no pase a mostrar comentarios internos por
descuido.

### Subsanar y Rechazar

Ambas acciones dejan de pedir un motivo suelto. Muestran la previsualización de
las observaciones con Sí más un cuadro de texto libre opcional. Al confirmar
viaja sólo ese texto libre: el motivo lo recalcula el backend, en orden
cronológico y sin duplicados, de modo que lo mostrado en pantalla es
previsualización y no fuente de verdad.

El motivo se compone **antes** de liberar el cupo y de tocar el estado. La
liberación de cupo ocurre al principio del método, común a las dos acciones, así
que componerlo dentro de cada bloque habría dejado el cupo liberado al devolver
el error de validación, justo lo contrario de lo que pide el requerimiento ("no
se modifica el estado del legajo").

Se quitó el truncado a 500 caracteres del motivo: los campos que lo persisten son
todos `TextField` y la concatenación de varias observaciones los supera con
facilidad, así que truncaba justo lo que hay que comunicar.

Validar (Aprobar) no cambia: no exige comentarios, no publica nada y mantiene sus
transiciones.

## Compatibilidad

- Se conservan los campos legacy del legajo (`subsanacion_tipo`,
  `subsanacion_motivo`, `subsanacion_solicitada_en`, `subsanacion_usuario`), el
  `HistorialValidacionTecnica` y los modelos `Subsanacion` /
  `SubsanacionObservacion`.
- Las observaciones de `Subsanacion` se derivan de los comentarios técnicos
  (RENAPER a `RENAPER`; ANSES y condición diagnóstica a `DOCUMENTACION`, que son
  ambas cuestiones de documentación respaldatoria), con fallback al parseo
  anterior del POST para los legajos que todavía no tienen comentarios nuevos.
- El endpoint de alta sigue aceptando el comentario libre previo, aunque la UI ya
  no lo ofrezca.
- No se migraron hacia atrás los legajos que ya estaban en SUBSANAR con motivo
  libre: los cubre el fallback.

## Decisiones tomadas fuera de la letra del issue

- Rechazar sin observaciones y sin texto libre devuelve error de validación. El
  punto 8 no lo dice (el 7 sí), pero Rechazar ya exigía motivo obligatorio y
  dejarlo pasar sería una regresión.
- Rechazar publica sólo las observaciones con Sí, aunque el punto 8 empiece
  diciendo "las observaciones técnicas registradas": el mismo punto aclara
  después "con respuesta Sí", y el punto 5 deja los No como internos.
- Se retiraron del formulario el textarea libre y el adjunto: el requerimiento
  enumera cuatro campos y ninguno es texto suelto.

## Corrección incluida

El badge de autoría etiquetaba como "Provincia" a cualquier superusuario, porque
preguntaba por el permiso de rol y un superusuario los tiene todos. Se etiqueta
por `is_territorial_user`, que es el mismo criterio con el que se decide qué
comentarios recibe la Provincia.

## Evidencia

`celiaquia/tests/test_comentarios_tecnicos_service.py` cubre el catálogo, la
validación de la combinación, la multi-alta, la concatenación cronológica sin
duplicados y la publicación selectiva.
`celiaquia/tests/test_comentarios_tecnicos_flujo.py` cubre los endpoints, la
visibilidad por rol y estado, y el comportamiento de Subsanar y Rechazar,
incluido el caso sin observaciones ni texto libre.
