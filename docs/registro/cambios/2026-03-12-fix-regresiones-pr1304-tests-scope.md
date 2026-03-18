# 2026-03-12 - Fix regresiones PR1304 (scope + tests)

## Resumen

Se corrigieron regresiones detectadas al validar el PR 1304:

1. Fixture de tests de `comedores` actualizado para soportar la nueva firma de `ComedorService.get_comedor_detail_object(..., user=...)`.
2. Manejo explícito de error en edición de relevamientos cuando falta `relevamiento_id` para evitar 500.
3. Test AJAX de edición de relevamiento ajustado al contrato actual (`relevamiento_id` + mock de chequeo scoped).

## Archivos tocados

- `comedores/conftest.py`
- `comedores/views/relevamientos.py`
- `comedores/tests.py`

## Validación ejecutada

- `docker compose exec django pytest -q tests/test_nomina_views_unit.py tests/test_pwa_mensajes_api.py tests/test_admisiones_service_botones_characterization_db.py comedores/tests.py`
- `docker compose exec django pytest -q tests/test_nomina_scope_access_db.py tests/test_audittrail_views_unit.py tests/test_comedor_service_characterization_db.py`

Resultado: ambas corridas en verde.
