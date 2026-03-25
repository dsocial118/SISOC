# 2026-03-25 - Solapa Responsables desde la organizacion del comedor

## Resumen
- La solapa `Responsables` del detalle de comedor paso a tomar sus datos desde la organizacion vinculada.
- Se retiraron de esa solapa los campos legacy propios del comedor (`referente`, `referente_2`, `responsable_tarjeta`, `aval_1`, `aval_2`).
- El detalle ahora oculta filas sin dato y tambien oculta los bloques de `Firmantes` y `Avales` cuando la organizacion no tiene registros asociados.

## Cambios realizados
- Archivo: `comedores/services/comedor_service/impl.py`
  - Se optimizo el queryset del detalle con `select_related` para `tipo_entidad` y `subtipo_entidad`.
  - Se agregaron `prefetch_related` para `organizacion.firmantes` con su `rol` y `organizacion.avales`.
- Archivo: `comedores/views/comedor.py`
  - Se agrego un builder de contexto presentacional para la solapa `Responsables`.
  - Se normalizo el formato visible de firmantes y avales para no mostrar etiquetas vacias.
- Archivo: `comedores/templates/comedor/comedor_detail.html`
  - Se rearmo el panel `Responsables` usando datos reales de la organizacion vinculada.
  - Se ocultaron campos sin valor y bloques vacios.

## Comportamiento visible
- Si el comedor tiene organizacion vinculada, se muestran sus datos institucionales en la solapa.
- Los firmantes se renderizan como `<rol>: <nombre> <cuit>` cuando hay datos.
- Los avales se renderizan como `Aval n: <nombre> <cuit>` cuando hay datos.
- Si no hay organizacion vinculada, la solapa muestra un estado vacio breve y explicito.
