# 2026-03-19 - Fix provincia RENAPER en detalle de expediente de Celiaquía

## Qué se corrigió
- En la validación RENAPER de `celiaquia/expedientes/<pk>`, la provincia del bloque RENAPER ahora se completa también cuando el servicio devuelve `provincia_api` (texto) y no `provincia` (PK local).
- Se agregaron fallbacks de compatibilidad para llaves de payload usadas por RENAPER en este flujo: `dni`/`documento`, `localidad_api`/`ciudad`, `piso_vivienda`/`piso_departamento`.

## Causa raíz
- El formateador de la vista `ValidacionRenaperView` asumía siempre `provincia` como clave numérica de `core.Provincia`.
- El servicio de consulta RENAPER actualmente devuelve en varios casos `provincia_api` como texto, por lo que la provincia quedaba vacía o en estado no resuelto en la comparación.

## Validación
- Test unitario de regresión agregado en `tests/test_validacion_renaper_view_unit.py`.
- Ejecución local:
  - `/home/juanikitro/SISOC/.venv/bin/python -m pytest -q tests/test_validacion_renaper_view_unit.py`
  - Resultado: `13 passed`.
