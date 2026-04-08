# 2026-04-07 - Fix defaults en formulario posterior de importación de Celiaquía

## Qué se cambió

- La edición de registros erróneos ya no muestra el campo `nacionalidad`; ahora envía siempre `Argentina` como valor por defecto.
- El modal de edición de legajo también fija `Argentina` y deja de exponer `nacionalidad` como campo editable.
- El backend deriva `municipio` a partir de la `localidad` seleccionada para mantener consistencia al guardar y al reprocesar.
- El frontend sincroniza `localidad -> municipio` tanto en registros erróneos como en la edición de legajo.

## Decisión de diseño

Se duplicó la protección en UI y backend:

- UI: ocultar el campo y sincronizar selects para reducir errores de carga.
- Backend: forzar `Argentina` y derivar `municipio` desde `localidad` para no depender solo del formulario.

## Validación

- `docker compose exec -T django pytest -q tests/test_celiaquia_expediente_view_helpers_unit.py celiaquia/tests/test_registros_erroneos_obligatorios.py celiaquia/tests/test_legajo_editar.py`
- `docker compose exec -T django black --check celiaquia/views/expediente.py celiaquia/views/legajo_editar.py celiaquia/tests/test_registros_erroneos_obligatorios.py celiaquia/tests/test_legajo_editar.py tests/test_celiaquia_expediente_view_helpers_unit.py`
- `docker compose exec -T django djlint celiaquia/templates/celiaquia/expediente_detail.html --check --configuration=.djlintrc`

## Impacto esperado

- Menos correcciones manuales en el flujo posterior a importar expedientes.
- Menor riesgo de inconsistencias entre localidad y municipio.
- Persistencia alineada con la regla operativa de nacionalidad fija en este formulario.
