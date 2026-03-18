# Fix regresiones de tests detectadas en GH Actions (`tests.log`)

Fecha: 2026-03-12

## Contexto
Se reportaron fallas en la corrida de tests de GitHub Actions (archivo `tests.log`).
El log mostraba 48 fallos inicialmente.
La dirección final del cambio fue: **no reintroducir compatibilidad para grupos/aliases legacy en runtime** y actualizar tests al modelo canónico de permisos y a la migración `Nomina -> Admision`.

## Qué se corrigió

1. Permisos canónicos en tests unitarios:
- Se actualizaron stubs de usuario para usar `is_authenticated` + `has_perm(...)` con codenames Django (`app_label.codename`), sin depender de `groups.filter(...).exists()`.
- Se ajustaron tests de Celiaquía, Admisiones, Centro y Acompañamientos a chequeos por permisos canónicos.

2. Tests afectados por `Nomina -> Admision`:
- Se migraron fixtures y creación de `Nomina` para usar `admision=...` en lugar de `comedor=...`.
- Se ajustaron aserciones y llamados esperados en tests de PWA y Comedores para IDs de admisión activa.

3. Tests de `MontoPrestacion`:
- Se actualizó el fixture de usuario con permisos para reflejar el control de acceso actual (sin fallback legacy).
- Se mantuvieron los escenarios de creación/edición/borrado/historial validando los mismos resultados funcionales.

4. Ajustes puntuales de datos de prueba:
- Se corrigieron datos duplicados en catálogo de actividades PWA para evitar colisiones con semilla inicial.
- Se actualizaron expectativas de contexto en tests unitarios donde cambió el tipo retornado (objeto de admisión activa en timeline).

## Validación ejecutada
- Re-ejecución del subset exacto de fallas listadas en `tests.log`:
  - `docker compose exec django bash -lc 'pytest -q -n 0 $(awk "/^FAILED /{print $2}" tests.log)'`
  - Resultado: **43 passed**.
- Re-ejecución por archivos fallados del log:
  - `docker compose exec django pytest -q tests/test_pwa_actividades_models.py comedores/tests.py relevamientos/tests.py tests/test_pwa_nomina_api.py core/tests/test_monto_prestacion_views.py centrodeinfancia/tests/test_intervencion_documentacion_permissions.py tests/test_acompanamiento_service_helpers_unit.py tests/test_celiaquia_expediente_view_helpers_unit.py tests/test_centro_views_unit.py tests/test_comedor_service_renaper_helpers_unit.py tests/test_comedor_views_unit.py tests/test_legajo_editar_view_unit.py tests/test_admisiones_service_helpers_unit.py tests/test_admisiones_web_views_unit.py`
  - Resultado: **187 passed**.

## Alcance y compatibilidad
- No se reintrodujo compatibilidad para grupos legacy en runtime.
- Se priorizó alinear tests con permisos canónicos y contratos actuales del código.
- Sin cambios en configuración de CI/tooling.
