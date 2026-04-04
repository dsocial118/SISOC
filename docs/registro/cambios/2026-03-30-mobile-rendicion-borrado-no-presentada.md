# Mobile rendición: borrado de rendiciones no presentadas

Fecha: 2026-03-30

## Qué cambió

- Se agregó en SISOC Mobile un botón para borrar una rendición desde su detalle.
- Antes de eliminar, la app muestra una confirmación explícita con un modal visual propio, en lugar del diálogo nativo del navegador.
- El borrado sólo está habilitado para rendiciones en `elaboracion` o `subsanar`.
- En el detalle editable, las acciones `Enviar a revisión` y `Borrar rendición` ahora comparten una misma fila.
- El botón principal de envío ocupa tres cuartos del ancho y el de borrado queda como acción secundaria en el cuarto restante.

## Backend

- Se expuso el endpoint mobile:
  - `POST /api/comedores/{id}/rendiciones/{rendicion_id}/eliminar/`
- El backend rechaza el borrado si la rendición ya fue presentada o finalizada.

## Mobile

- El botón `Borrar rendición` aparece sólo cuando la rendición todavía es editable.
- Luego de eliminar, la app vuelve al listado de rendiciones del mismo contexto.

## Validación

- `docker-compose exec django pytest tests/test_pwa_comedores_api.py -k "eliminar_rendicion_mobile_en_elaboracion or eliminar_rendicion_mobile_rechaza_revision"`
- `npm run build` en `mobile/`
