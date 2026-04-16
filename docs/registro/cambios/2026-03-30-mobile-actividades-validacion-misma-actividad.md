# Actividades mobile: validación por misma actividad

## Fecha
- 2026-03-30

## Cambio
- Se ajustó la validación de horarios de actividades.
- Ahora se permiten actividades distintas en el mismo día y franja horaria.
- Solo se rechaza cuando la misma actividad queda duplicada con horarios cruzados en el mismo día.

## Backend
- La validación de solapamiento en `ActividadEspacioPWACreateUpdateSerializer` ahora filtra también por `catalogo_actividad`.

## Mobile
- La validación local del formulario de actividades replica la misma regla de negocio.

## Validación
- `docker-compose exec django pytest tests/test_pwa_actividades_api.py`
- `npm run build` en `mobile/`
