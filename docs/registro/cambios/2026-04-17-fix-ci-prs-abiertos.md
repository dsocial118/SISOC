# 2026-04-17 - Fix compartido para CI en PRs abiertos

## Contexto

Varios PRs abiertos de `juanikitro` estaban fallando en CI por una combinacion de:

- deteccion incorrecta de archivos cambiados en `lint` cuando GitHub Actions hace checkout shallow del merge commit del PR,
- una regresion en `celiaquia` donde el registro erroneo dejo de forzar nacionalidad Argentina,
- un test unitario de `comedores` que no reflejaba el refactor actual del queryset de nomina.

## Cambios

- `scripts/ci/pr_lint_tools.py`
  - agrega fallback via API de GitHub para listar archivos del PR cuando el rango `base..head` no esta disponible localmente.
- `celiaquia/views/expediente.py`
  - restaura el default de nacionalidad Argentina en `_aplicar_defaults_registro_erroneo`.
- `tests/test_comedor_service_renaper_helpers_unit.py`
  - ajusta el doble `_NominaQS` para cubrir el encadenamiento actual de queryset.
- `tests/test_pr_lint_tools_unit.py`
  - agrega cobertura para el fallback via API y conserva el fallback git como ultimo recurso.

## Impacto

- Reduce falsos negativos de `black` en PRs abiertos por checkouts shallow.
- Alinea el comportamiento de `celiaquia` con la expectativa ya cubierta por tests.
- Evita fallos compartidos en ramas abiertas sin tocar el flujo funcional de cada PR.
