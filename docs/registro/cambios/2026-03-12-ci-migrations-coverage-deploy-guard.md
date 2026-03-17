# 2026-03-12 - CI con migrations-check, coverage-gate y deploy-guard

## Resumen

Se agregaron tres controles de CI para endurecer la calidad antes de merge/deploy:

- `migrations_check`: valida que no existan cambios de modelos sin migración.
- `coverage_gate`: ejecuta tests con cobertura mínima.
- `deploy_guard`: verifica que los checks críticos estén en estado válido.

## Detalle técnico

- Archivo modificado: `.github/workflows/tests.yml`
  - Se agregó permiso `checks: read`.
  - Nuevo job `migrations_check`:
    - levanta Docker,
    - espera MySQL,
    - corre `python manage.py makemigrations --check --dry-run`.
  - Nuevo job `coverage_gate` (solo `pull_request`):
    - corre `pytest -n auto --cov=. --cov-fail-under=75`.
  - Nuevo job `deploy_guard` (solo `pull_request`):
    - depende de `smoke`, `tests`, `migrations_check`, `coverage_gate`,
    - consulta check-runs del SHA del PR y exige estado válido para:
      - `gitleaks`, `black`, `djlint`, `pylint`,
      - `smoke`, `tests`, `migrations_check`, `coverage_gate`.

## Impacto

- Se detectan migraciones faltantes antes del merge.
- Se evita degradación de cobertura por debajo de 75% en PRs.
- Se agrega una compuerta explícita de calidad para merge/deploy basada en checks requeridos.
