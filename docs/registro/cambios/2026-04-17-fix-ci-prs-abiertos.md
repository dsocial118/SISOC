# 2026-04-17 - Fix compartido para CI en PRs abiertos

## Contexto

Varios PRs abiertos de `juanikitro` estaban fallando en CI por una combinacion de:

- deteccion incorrecta de archivos cambiados en `lint` cuando GitHub Actions hace checkout shallow del merge commit del PR,
- desalineacion entre un unit test de `celiaquia` y el comportamiento esperado de nacionalidad editable en registros erroneos,
- un test unitario de `comedores` que no reflejaba el refactor actual del queryset de nomina.

## Cambios

- `scripts/ci/pr_lint_tools.py`
  - agrega fallback via API de GitHub para listar archivos del PR cuando el rango `base..head` no esta disponible localmente.
- `celiaquia/views/expediente.py`
  - conserva la autocompletacion de municipio por localidad sin forzar nacionalidad en `_aplicar_defaults_registro_erroneo`.
- `tests/test_celiaquia_expediente_view_helpers_unit.py`
  - alinea la expectativa del helper con la nacionalidad editable que ya validan los tests integrales.
- `tests/test_comedor_service_renaper_helpers_unit.py`
  - evita construir un `Subquery` real sobre un doble de queryset, stubbeando el builder que prepara la nomina.
- `tests/test_pr_lint_tools_unit.py`
  - agrega cobertura para el fallback via API y conserva el fallback git como ultimo recurso.

## Impacto

- Reduce falsos negativos de `black` en PRs abiertos por checkouts shallow.
- Mantiene la nacionalidad editable en `celiaquia` y corrige el autocompletado solo donde corresponde.
- Evita fallos compartidos en ramas abiertas sin tocar el flujo funcional de cada PR.
