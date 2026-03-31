# 2026-03-12 - Fix workflow de pytest en GitHub Actions

## Resumen

Se corrigió una inconsistencia en `.github/workflows/tests.yml` que impedía el disparo correcto del pipeline de tests en PR.

## Causa raíz

El job `deploy_guard` seguía referenciando jobs antiguos (`tests` y `coverage_gate`) que ya no existen luego de la unificación en el job `pytest`.

Esto dejaba el workflow inválido en GitHub Actions (`needs` apuntando a jobs inexistentes), bloqueando la ejecución esperada.

## Cambios aplicados

- Archivo modificado: `.github/workflows/tests.yml`
  - `deploy_guard.needs`: se reemplazó `tests` + `coverage_gate` por `pytest`.
  - Lista `required` del script de guard: se reemplazó `tests` por `pytest` y se removió `coverage_gate`.

## Impacto

- El workflow vuelve a ser válido y `pytest` puede ejecutarse en eventos `pull_request` a `development/main`.
- Se mantiene el gate de cobertura porque el job `pytest` ya corre con `--cov-fail-under=75`.
