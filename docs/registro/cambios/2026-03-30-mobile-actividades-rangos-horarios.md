# Mobile actividades: rangos horarios y agenda semanal

## Fecha
- 2026-03-30

## Alcance
- Se reemplazó el esquema operativo de horario único por `hora_inicio` y `hora_fin` en actividades PWA.
- Se agregó validación para evitar solapamientos de actividades activas en el mismo espacio y día.
- Se actualizó Mobile para cargar rangos horarios y mostrar una vista tipo agenda semanal.

## Backend
- `ActividadEspacioPWA` ahora incorpora `hora_inicio` y `hora_fin`.
- La API sigue devolviendo `horario_actividad`, pero ahora como etiqueta derivada del rango horario.
- El serializer de create/update valida:
  - hora de inicio obligatoria
  - hora de fin obligatoria
  - `hora_fin > hora_inicio`
  - ausencia de superposición con otras actividades activas del mismo espacio y día
- Se agregó la migración `0011_actividadespaciopwa_hora_inicio_hora_fin.py` para:
  - incorporar los nuevos campos
  - migrar horarios existentes desde `horario_actividad`
  - inferir fin por duración o, si no existe dato suficiente, por default de una hora

## Mobile
- El formulario de actividades ahora usa `Hora de inicio` y `Hora de fin`.
- La validación local replica el chequeo de superposición dentro de la misma carga.
- El listado suma una `Agenda semanal` por día para ver rápidamente el calendario operativo del espacio.

## Testing y validación
- `docker-compose exec django pytest tests/test_pwa_actividades_api.py`
- `docker-compose run --rm django pytest tests/test_pwa_nomina_api.py`
- `docker-compose exec django python manage.py makemigrations --check`
- `npm run build` en `mobile/`

## Notas
- La API conserva `horario_actividad` para no romper consumos existentes que solo muestran el rango en texto.
- Falta aplicar la migración nueva en el entorno operativo con `python manage.py migrate pwa`.
