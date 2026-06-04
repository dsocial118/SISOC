# VPSL: bandeja, exportaciones y laboratorio masivo

## Contexto

Se toma la documentacion funcional de VPSL como hoja de ruta, contemplando cambios posteriores de producto.

## Cambios

- La bandeja de itinerarios incorpora filtros por busqueda, estado, provincia, localidad y rango de fechas.
- Los usuarios no administradores quedan restringidos a itinerarios/jornadas/casos de laboratorio de la provincia asignada en su perfil provincial.
- Se agregan exportaciones CSV para detalle de itinerario y detalle de jornada.
- El bloque de casos de laboratorio en jornada permite scroll y actualizacion masiva de varios casos seleccionados cuando comparten estado.
- Se agrega vehiculo asignado a la jornada y sugerencia incremental editable para numero de acta en registro nominal.
- El resumen de cierre diario suma contadores de no requiere anteojos y derivados, manteniendo actualizacion automatica.
- Se permite crear multiples jornadas en una misma fecha para un mismo itinerario, manteniendo bloqueo solo para duplicado exacto de fecha y sede.

## Validacion

- `docker compose -f docker-compose.yml exec -T django python manage.py check`
- `docker compose -f docker-compose.yml exec -T django pytest ver_para_ser_libre/tests/test_workflow.py -q`
- `docker compose -f docker-compose.yml exec -T django python manage.py migrate ver_para_ser_libre`
