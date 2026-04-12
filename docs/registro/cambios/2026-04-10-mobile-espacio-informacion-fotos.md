# Mobile espacio: fotos en información institucional

## Cambio

- Se habilita la carga de hasta 3 fotos por espacio desde la pantalla `Información`.
- Las fotos se muestran al final de la pantalla en un carrusel horizontal.
- Las miniaturas del carrusel se reducen y cada foto se puede abrir en vista ampliada al tocarla.
- Las acciones `Tomar foto` y `Galería` se presentan como tiles visuales con iconos y mejor área táctil.
- La API mobile expone el alta de imágenes del comedor bajo `POST /api/comedores/{id}/imagenes/`.
- Se normaliza el archivo comprimido en mobile para conservar tipo/extensión válidos al subir JPG, PNG o WebP.
- El backend rechaza imágenes de espacio mayores a 3 MB con un mensaje de validación explícito.

## Alcance

- `comedores/api_views.py`
- `mobile/src/api/spacesApi.ts`
- `mobile/src/device/media.ts`
- `mobile/src/features/home/SpaceDetailPage.tsx`
- `tests/test_comedor_form_unit.py`
- `tests/test_pwa_comedores_api.py`
