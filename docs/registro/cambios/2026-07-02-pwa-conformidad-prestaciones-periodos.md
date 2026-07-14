# PWA conformidad de prestaciones por periodo calendario

## Cambio

La conformidad de prestaciones en la PWA deja de depender de los periodos calculados por convenio. El usuario puede seleccionar un periodo calendario en formato mes/año y registrar la conformidad para ese periodo.

## Reglas vigentes

- La seleccion del periodo queda disponible para todos los programas con acceso al espacio.
- El backend acepta cualquier mes calendario (`YYYY-MM`) y lo persiste como primer dia del mes.
- No se valida que el periodo sea vencido ni que pertenezca a una ventana de convenio.
- La unicidad se mantiene por espacio y periodo: no se permite registrar dos conformidades para el mismo mes del mismo comedor.

## Validacion

- `docker compose exec django pytest tests/test_pwa_comedores_api.py`
- `docker compose exec django pytest tests/test_comedores_utils_unit.py`
- `npm run build` en `mobile/`
