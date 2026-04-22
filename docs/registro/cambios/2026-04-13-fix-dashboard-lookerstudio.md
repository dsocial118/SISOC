# Fix dashboard Looker Studio

## Problema

La vista `dashboard/<slug>/` intentaba embeber cualquier `tablero.url` en un `iframe`.
Con Looker Studio eso fallaba cuando se cargaba la URL compartible comun del reporte,
porque Google solo permite embeber el formato generado desde `File > Embed report`.

## Cambio aplicado

- `Tablero.get_embed_url()` ahora convierte URLs compartibles de Looker Studio al
  formato `/embed/reporting/...` antes de renderizar el iframe.
- La pantalla del tablero agrega una accion para abrir el reporte en una pestana
  nueva y muestra una pista explicita para corregir la URL si se siguio cargando
  un link compartible normal.
- El CSP de SISOC agrega `lookerstudio.google.com` y `datastudio.google.com` en
  `frame-src` para no bloquear embebidos validos cuando el header pase a enforcement.

## Impacto

- No cambia el comportamiento de Power BI ni de otros proveedores.
- La configuracion en admin queda mas clara para futuros tableros de Looker Studio.
