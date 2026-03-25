# 2026-03-25 - Solapa Responsables desde la organización del comedor

## Resumen
- La solapa `Responsables` del detalle de comedor pasó a tomar sus datos desde la organización vinculada.
- Se retiraron de esa solapa los campos legacy propios del comedor (`referente`, `referente_2`, `responsable_tarjeta`, `aval_1`, `aval_2`).
- El detalle ahora oculta filas sin dato y también oculta los bloques de `Firmantes` y `Avales` cuando la organización no tiene registros asociados.

## Cambios realizados
- Archivo: `comedores/services/comedor_service/impl.py`
  - Se optimizó el queryset del detalle con `select_related` para `tipo_entidad` y `subtipo_entidad`.
  - Se agregaron `prefetch_related` para `organización.firmantes` con su `rol` y `organización.avales`.
- Archivo: `comedores/views/comedor.py`
  - Se agregó un builder de contexto presentacional para la solapa `Responsables`.
  - Se normalizó el formato visible de firmantes y avales para no mostrar etiquetas vacías.
- Archivo: `comedores/templates/comedor/comedor_detail.html`
  - Se rearmó el panel `Responsables` usando datos reales de la organización vinculada.
  - Se ocultaron campos sin valor y bloques vacíos.

## Comportamiento visible
- Si el comedor tiene organización vinculada, se muestran sus datos institucionales en la solapa.
- Los firmantes se renderizan como `<rol>: <nombre> <cuit>` cuando hay datos.
- Los avales se renderizan como `Aval n: <nombre> <cuit>` cuando hay datos.
- Si no hay organización vinculada, la solapa muestra un estado vacío breve y explícito.
