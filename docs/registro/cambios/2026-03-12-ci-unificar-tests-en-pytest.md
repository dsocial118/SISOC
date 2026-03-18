# 2026-03-12 - CI: unificar tests en `pytest` con cobertura

## Resumen

Se simplificó el workflow de tests para evitar duplicación:

- Se eliminó el job `tests`.
- El job con cobertura se renombró a `pytest`.
- `deploy_guard` ahora exige `pytest` como check requerido.

## Detalle técnico

- Archivo modificado: `.github/workflows/tests.yml`
  - Renombre de job `coverage_gate` a `pytest`.
  - Eliminación del job `tests` (que corría `pytest -n auto` sin cobertura).
  - Actualización de `deploy_guard`:
    - `needs`: ahora depende de `smoke`, `migrations_check`, `pytest`.
    - `required` checks: reemplaza `tests` y `coverage_gate` por `pytest`.

## Impacto

- Se mantiene la validación de test suite y además la cobertura mínima (`--cov-fail-under=75`) en un único job.
- Disminuye tiempo/costo de CI al evitar ejecutar dos veces casi la misma suite.
