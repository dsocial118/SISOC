# 2026-06-09 - Autocomplete de territorial en alta de relevamiento

## Resumen
- El modal de alta de relevamiento paso de un select a un input con autocompletado para buscar territoriales escribiendo su nombre.
- La lista de territoriales sigue saliendo del cache compartido en `static/custom/js/comedordetail_territorial_cache.js`.
- Se conserva el boton de refresco/sincronizacion de cache.

## Cambios realizados
- Archivo: `relevamientos/templates/relevamiento_list.html`
  - Se reemplazo el select de territorial por un input de texto con sugerencias.
  - Se agrego un campo oculto con el payload JSON que sigue enviando el backend.
- Archivo: `static/custom/js/comedordetail_territorial_cache.js`
  - Se agrego una lista en memoria con los territoriales cargados desde el cache/API.
  - Se implemento filtrado por escritura para poblar el autocomplete.
  - Se mantuvo la sincronizacion manual y la recarga del cache.
- Archivo: `relevamientos/tests.py`
  - Se actualizo la prueba de renderizado para verificar el nuevo input y los contenedores de sugerencias.

## Comportamiento observable
- El usuario puede escribir parte del nombre del territorial y ver coincidencias en tiempo real.
- Al elegir una sugerencia, el formulario conserva el mismo contrato de envio y crea el relevamiento con el territorial seleccionado.