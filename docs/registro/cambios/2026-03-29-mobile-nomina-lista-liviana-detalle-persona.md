# Mobile nómina: lista liviana y detalle por persona

## Qué cambió

- La pantalla de nómina mobile ahora mantiene el tablero resumen y el buscador.
- El listado principal de personas se simplificó para mostrar solo el nombre.
- Se agregó una página específica de detalle por persona dentro de Mobile.
- La navegación nueva usa:
  - `GET /api/pwa/espacios/{comedor_id}/nomina/` para el índice
  - `GET /api/pwa/espacios/{comedor_id}/nomina/{nomina_id}/` para el detalle
  - `GET /api/pwa/espacios/{comedor_id}/nomina/{nomina_id}/historial-asistencia/` para historial

## Objetivo

- Reducir el peso visual y técnico de la pantalla inicial de nómina.
- Evitar que el detalle de una persona cargue dentro del listado completo.
- Facilitar la búsqueda operativa por apellido o DNI.
