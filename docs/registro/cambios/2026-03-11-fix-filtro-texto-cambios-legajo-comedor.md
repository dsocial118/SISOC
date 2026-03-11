# 2026-03-11 - Fix filtro "Texto en cambios" en historial de legajo comedor

## Contexto
- En el historial de auditoría de instancia (legajo comedor), al editar `nombre` y buscar ese valor en el filtro "Texto en cambios", no se devolvían resultados.
- Se verificó que existen eventos con `changes` JSON poblado y `changes_text` vacío.

## Cambios aplicados
- Se ajustó `audittrail/services/query_service/impl.py` para que el filtrado por texto y por campo consulte de forma combinada los lookups disponibles en `changes` y `changes_text`.
- Se mantuvo el camino de FULLTEXT para MySQL sobre `changes_text`, agregando fallback OR contra búsqueda textual en cambios para no perder coincidencias cuando `changes_text` está vacío.
- Se agregaron/actualizaron tests unitarios en `tests/test_audittrail_views_unit.py` para cubrir la nueva semántica de búsqueda.

## Impacto esperado
- El filtro "Texto en cambios" vuelve a encontrar valores cambiados del legajo comedor cuando están presentes en `changes` aunque `changes_text` no tenga contenido.
- No se cambia contrato de URL ni payload de la vista de auditoría.

## Validación
- `docker compose exec django pytest -n auto tests/test_audittrail_views_unit.py` (16 tests OK).
- Verificación manual en shell sobre datos reales: búsqueda por valor nuevo de `nombre` en historial de instancia devuelve coincidencias.

## Riesgos y rollback
- Riesgo principal: consultas con OR sobre dos campos pueden aumentar costo en rangos amplios.
- Mitigación: se conservan límites de rango ya existentes en formulario/export y ruta FULLTEXT para MySQL.
- Rollback: revertir cambios en `audittrail/services/query_service/impl.py` y `tests/test_audittrail_views_unit.py`.
