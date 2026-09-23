# 2026-09-23 - "Volver" unificado en todas las pantallas (#2460)

## Contexto
- El boton "Volver" estaba implementado pantalla por pantalla, con posicion y
  estilo distintos: margen derecho junto a las opciones de archivo, debajo de la
  carga de archivos, margen izquierdo, o directamente ausente.
- Relevamiento: de las **327 pantallas** (templates que extienden
  `includes/main.html`), **138 tenian algun "Volver"** con markup propio
  (41 `btn btn-secondary`, 7 `btn-sm btn-primary`, 5 `btn-outline-secondary`,
  `btn-cancel`, etc.), mas un tercer estilo (`poncho-volver`, pildora blanca) en
  el componente `search_bar.html`.
- Las referencias del issue diferian entre si: el detalle de comedores usaba
  azul arriba a la izquierda; la edicion de admisiones tecnicas, gris.
- "Que persistan los filtros" no funcionaba: `navigator.js` guardaba `lastUrl`
  solo si el link de origen tenia la clase `.link-handler`, cosa que casi ningun
  listado usa.

## Cambios aplicados
- `templates/components/back_button.html` (nuevo): markup canonico. Gris
  (`btn btn-secondary btn-sm`), con flecha, arriba a la izquierda.
- `templates/includes/main.html`: lo incluye **una sola vez**, antes del titulo
  de pagina, de modo que aparece en las 327 pantallas sin tocar cada template.
- `static/custom/js/volver.js` (nuevo): mantiene una pila de URLs visitadas en
  `sessionStorage` **con querystring**, asi "Volver" regresa al listado tal como
  estaba filtrado. Cascada de resolucion: pila de navegacion -> referrer del
  mismo origen -> `volver_url` que declare la vista -> `history.back()`.
  Se carga desde `scripts/mainscripts.html`.
- `core/context_processors.boton_volver` + alta en `config/settings.py`: define
  `ocultar_volver`, `volver_url` y `volver_texto` para que el componente nunca
  resuelva variables inexistentes (hay un test en VAT que falla si un render
  loguea "Exception while resolving variable").
- `static/custom/css/custom.css`: estilos de `.sisoc-volver-barra`/`.sisoc-volver`
  (se oculta al imprimir).
- **Limpieza**: se removieron **119 botones "Volver" de navegacion en 110
  templates**, junto con los wrappers que quedaron vacios. Incluye las variantes
  con etiqueta propia ("Volver al CDI", "Volver a la nomina", "Volver al
  listado", ...), que quedan cubiertas por el boton global.
- `templates/components/search_bar.html`: se saco la rama `back_url`/`back_text`
  (la pildora blanca `poncho-volver`) y el parametro de los 8 includes que lo
  pasaban.
- `core/views.inicio_view`: pasa `ocultar_volver=True` por ser la pantalla raiz.

## Decisiones y limites
- **Se conservan 31 "Volver" que funcionan como cancelar de un formulario** (los
  que conviven con un `type="submit"`): no son navegacion, son descartar la
  edicion, y sacarlos dejaria formularios sin salida junto a "Guardar". Queda
  pendiente, si UX lo pide, renombrarlos a "Cancelar".
- No se tocaron `templates/403.html`, `404.html` y `500.html`: ahi "volver al
  inicio" es un link dentro de un parrafo, no un boton.
- Tampoco el `prev_text='Volver'` de `components/pagination.html`, que es
  paginado, no navegacion.

## Impacto esperado
- Todas las pantallas muestran el mismo "Volver", gris, arriba a la izquierda.
- Al volver desde un detalle se recupera el listado con sus filtros aplicados,
  porque la pila guarda la URL completa.
- Entrar directo por URL (pestaña nueva, link compartido) cae al referrer o a la
  raiz: no hay pila previa que consultar.

## Validación
- `pytest -n auto`: 5453 passed, 14 skipped. Test nuevo
  `tests/test_boton_volver_unificado.py` (6), que incluye un test de arquitectura
  que falla si alguna pantalla vuelve a declarar su propio boton de navegacion.
- `tests/test_csv_export_architecture.py` sigue fallando, pero ya fallaba antes
  (rompe al decodificar un archivo `cp1252` de `xlwt`).
- `black` y `djlint --check` sobre lo tocado. Se descarto el reformateo masivo
  que `djlint --reformat` habia introducido en 4 templates que no estaban
  formateados de antes, para no mezclar formateo con el cambio funcional.

## Riesgos y rollback
- Riesgo principal: alguna pantalla dependia visualmente del boton removido
  (por ejemplo una fila de acciones que ahora queda con un solo elemento). El
  diff es de 89 inserciones / 473 borrados en 126 archivos: conviene una pasada
  visual por las pantallas mas usadas antes de mergear.
- Si una pantalla necesita un destino fijo, la vista pasa `volver_url`; si no
  debe mostrarlo, `ocultar_volver=True`.
- Rollback: revertir el commit. No hay migraciones.
