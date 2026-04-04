# Mobile actividades: duración derivada del rango horario

## Fecha
- 2026-03-30

## Cambio
- Se eliminó `duracion_actividad` del modelo y del contrato API de actividades PWA.
- La duración ya no se carga manualmente en Mobile.
- La interfaz ahora la deriva directamente desde `hora_inicio` y `hora_fin`.

## Backend
- Se removió el campo `duracion_actividad` de `ActividadEspacioPWA`.
- Se agregó la migración `0012_remove_actividadespaciopwa_duracion_actividad.py`.
- La API de actividades mantiene `hora_inicio`, `hora_fin` y `horario_actividad` como etiqueta derivada.

## Mobile
- El formulario de alta/edición de actividades ya no pide duración.
- Los lugares que mostraban duración ahora la calculan a partir del rango horario.

## Validación
- `docker-compose exec django pytest tests/test_pwa_actividades_api.py`
- `docker-compose run --rm django pytest tests/test_pwa_nomina_api.py`
- `docker-compose exec django python manage.py makemigrations --check`
- `npm run build` en `mobile/`

## Nota
- Falta aplicar la migración nueva en el entorno operativo con `python manage.py migrate pwa`.
