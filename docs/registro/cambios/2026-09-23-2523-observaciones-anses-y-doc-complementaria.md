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

Pendiente de implementación. Ver el análisis de alcance en el PR.
