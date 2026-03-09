# Fix PR 1291: colaboradores PWA, encoding y limpieza de imports

## Contexto
Se corrigieron issues detectados en revisión del PR 1291:
- conflicto de unicidad al recrear y volver a dar de baja colaboradores PWA con el mismo DNI;
- archivos con mojibake/BOM;
- import duplicado en `users/api_views.py`.

## Cambios realizados
- `pwa/models.py`
  - `UniqueConstraint` de colaboradores ajustada a `("comedor", "dni")`.
- `pwa/migrations/0004_mysql_colaborador_unique_fix.py`
  - sincronizada con el nuevo constraint `uniq_colaborador_pwa_dni_por_comedor`.
- `pwa/services/colaboradores_service.py`
  - `create_colaborador` ahora reactiva el registro inactivo existente para el mismo `comedor + dni` en lugar de crear duplicados.
- `users/api_views.py`
  - eliminado import duplicado de `UserContextSerializer`.
- Limpieza de mojibake/BOM en:
  - `centrodefamilia/services/consulta_renaper/impl.py`
  - `docs/implementaciones/pwa_backend.md`
  - `pwa/services/nomina_service.py`
  - `pwa/models.py`
  - `pwa/migrations/0005_actividades_pwa.py`
  - `tests/test_pwa_actividades_models.py`
- `tests/test_pwa_colaboradores_api.py`
  - nuevo test de regresión: ciclo crear/baja/recrear/baja con mismo DNI.

## Impacto
- Evita `IntegrityError` en baja lógica repetida de colaboradores.
- Mantiene un único colaborador por `comedor + dni` reutilizando la misma fila por reactivación.
- Corrige textos corruptos por encoding y elimina BOM en archivos afectados.
