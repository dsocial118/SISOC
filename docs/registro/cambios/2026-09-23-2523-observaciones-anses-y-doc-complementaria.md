# Celiaquía: observaciones de CODEM en ANSES y documentación complementaria al subsanar

Ticket 2523. Rama `CeliaquiaTk_2523`.

El ticket trae dos pedidos de tamaño muy distinto. Se implementan en etapas
dentro de un mismo PR.

## Parte 1 — Dos observaciones nuevas en el desplegable de ANSES

### Pedido

Incorporar al desplegable de Observaciones – ANSES de Comentarios Técnicos:

- «Enviar constancia de CODEM/ANSES, ya que la misma se encuentra vencida.
  Recordar que tiene una validez de 30 días.»
- «El CODEM vinculado contiene un CUIL inexistente. Se solicita subir el que
  corresponde.»

Manteniendo las reglas de visibilidad, publicación y asociación al legajo del
resto de las observaciones, y sin tocar «Otros».

### Solución

Dos tuplas nuevas en `_OBSERVACIONES_ANSES` (`celiaquia/comentarios_tecnicos.py`),
con los códigos `ANSES_CODEM_VENCIDO` y `ANSES_CUIL_INEXISTENTE`.

**No hay migración ni cambio de comportamiento.** El catálogo del issue #2318
vive como constantes, no como tabla (decisión documentada en el docstring del
módulo: los textos cambian muy poco y una tabla exigiría fixture + data
migration, que además no corre en los tests). Todo lo demás se propaga solo:

- el desplegable se arma desde `catalogo_serializable()`, que se embebe como
  JSON en `expediente_detail.html`;
- la validación del alta pasa por `es_codigo_valido()`, que deriva del mismo
  catálogo;
- el texto queda snapshoteado en `HistorialComentarios.comentario`, así que las
  reglas de publicación a Provincia y de concatenación en Subsanar/Rechazar
  aplican sin cambios.

Por eso las «mismas reglas» que pide el ticket no hubo que replicarlas: son las
mismas por construcción.

### Tests

En `celiaquia/tests/test_comentarios_tecnicos_service.py`:

- `test_catalogo_anses_incluye_las_observaciones_de_codem` compara los textos
  completos. Son normativos —los define el área y es literalmente lo que se le
  comunica a la Provincia—, así que un cambio de redacción tiene que romper el
  test y pasar por revisión.
- `test_codigos_del_catalogo_entran_en_el_campo_que_los_persiste` recorre los
  tres tipos y verifica `len(codigo) <= MAX_LEN_CODIGO_OBSERVACION`. Es una
  guarda para altas futuras: un código más largo que la columna no falla al
  definirlo sino recién al guardar el comentario.

Suite de celiaquía: 321 passed.

## Parte 2 — Documentación complementaria en la acción Subsanar

### Pedido

Al solicitar una subsanación, Nación puede adjuntar uno o más archivos como
documentación complementaria de las observaciones técnicas. Es opcional y no
puede bloquear la acción. No cuelga de una observación puntual (RENAPER, ANSES o
condición diagnóstica) sino de la solicitud entera, y la Provincia tiene que
poder consultarla junto con las observaciones.

### Decisión: un campo `origen`, no un modelo nuevo

`SubsanacionArchivo` ya existía con `archivo`, `descripcion`, `usuario` y
`creado_en`. Se le agregó `origen` (`PROVINCIA` / `NACION`) en lugar de crear un
modelo aparte, por dos razones:

1. `templates/components/legajo_archivos_requeridos.html` ya renderizaba
   `sub.archivos.all` en el bloque "Historial de subsanaciones", y ese bloque no
   está detrás de `is_prov`. La visibilidad para la Provincia sale de ahí.
2. La auditoría que pide el ticket ya estaba: usuario y fecha en el propio
   `SubsanacionArchivo`, y estado anterior/nuevo en el `HistorialValidacionTecnica`
   que `RevisarLegajoView._subsanar` crea en la misma transacción. No hizo falta
   un modelo de auditoría.

La migración `0008` es de esquema puro, con `default="PROVINCIA"`: las filas
existentes son todas respuestas de la Provincia por definición, así que el
default las clasifica bien sin data migration.

### El riesgo que había que cubrir

`SubsanacionService.tiene_evidencia()` decidía si la Provincia ya había
respondido con un `subsanacion.archivos.exists()` sin filtro. Es lo que habilita
el botón "Confirmar subsanación" del lado provincial. Metiendo los archivos de
Nación en la misma relación, **pedir una subsanación con documentación adjunta
habría dado la subsanación por respondida sin que la Provincia subiera nada.**

Por eso toda lectura que responda "¿ya respondió la Provincia?" filtra ahora por
origen:

- `SubsanacionService.tiene_evidencia()` (y `legajos_sin_evidencia()`, que lo usa);
- el conteo de la respuesta JSON en `SubsanacionRespuestaUploadView`;
- el bloque "Archivos corregidos (evidencia nueva)" del componente, que si no
  mostraba los archivos de Nación como si fueran respuesta provincial.

`SubsanacionService.responder()` ahora marca `origen=PROVINCIA` explícitamente en
lugar de confiar en el default.

### Decisiones de implementación

- **Validación antes de la transacción.** `RevisarLegajoView._subsanar` valida el
  lote completo antes de tocar el estado del legajo. Un archivo inválido devuelve
  400 y no deja la subsanación hecha a medias.
- **Límites en `celiaquia/validators.py`**, siguiendo la convención por app del
  repo (`dispositivos/validators.py`, `insumos/validators.py`): PDF/JPG/PNG, 10 MB
  por archivo, hasta 5 archivos. Definido con producto. La extensión se valida
  siempre porque el content type lo declara el cliente y es falsificable.
- **Los errores se muestran dentro del modal**, no sólo en la zona de alertas de
  la página. Detectado en QA: el motivo del rechazo sí se generaba y `showAlert`
  lo concatenaba bien, pero se pintaba arriba de la página, detrás del backdrop
  del modal, así que el usuario veía que la acción fallaba sin saber por qué.
- **Validación en el cliente además de la del backend.** El `accept` del input
  hace que el explorador de archivos filtre las extensiones no permitidas, y eso
  es mudo: el archivo simplemente no aparece en el diálogo. Ahora se valida
  extensión, tamaño y cantidad al elegir los archivos y se avisa en el momento.
  Los límites viajan al template en el contexto (`complementaria_*`) y de ahí al
  JS por `data-*`, así que siguen declarados en un solo lugar. El backend
  revalida igual: lo del cliente es comodidad, no control.
- **`SubsanacionArchivo.nombre_archivo`** devuelve el basename. Los templates
  mostraban `archivo.name`, que incluye la carpeta de `upload_to` y en pantalla
  quedaba como `legajos/subsanaciones/constancia-2026-09-07.pdf`. Se corrigió en
  los tres bloques del componente, incluidos los que ya existían.
- **`Subsanacion.archivos_de_provincia` / `.archivos_de_nacion`** filtran en
  Python sobre `archivos.all()` en vez de usar `.filter()`. El detalle del
  expediente prefetchea `subsanaciones__archivos`; un `.filter()` rompería ese
  caché y agregaría una consulta por subsanación y por bloque del template.

### Fuera de alcance (deuda registrada)

- La carga de subsanación de la **Provincia** sigue sin validar tipo ni tamaño
  (`celiaquia/views/subsanacion.py`). Es un problema previo y se deja para su
  propio ticket.
- `MEDIA_URL` se sirve estático y el template linkea `archivo.url` directo, así
  que quien tenga la URL descarga el archivo sin pasar por permisos. Ya era así
  para toda la subsanación; el ticket pide que la documentación sea visible para
  la Provincia "cuando corresponda", y eso se cumple a nivel UI pero no a nivel
  URL. Cambiarlo implica servir los adjuntos por vista protegida, que es un
  evolutivo aparte.

### Tests

`celiaquia/tests/test_subsanacion_documentacion_complementaria.py` (12 casos).
El central es `test_la_documentacion_de_nacion_no_cuenta_como_respuesta`, que fija
la regresión descrita arriba. Los demás cubren el alta con origen y usuario, que
la ausencia de archivos no bloquee, que la respuesta de la Provincia sí cuente
como evidencia, y las tres validaciones (extensión, tamaño, cantidad) verificando
además que el legajo quede intacto cuando el lote es inválido.

Suite de celiaquía: 333 passed.
