# 2026-03-13 - CI de tests en contenedores one-off

## Resumen

Se ajustó `.github/workflows/tests.yml` para que los jobs `smoke` y `pytest` ejecuten `pytest` con `docker compose run --rm` en lugar de `docker compose exec` sobre el servicio `django` ya levantado.

## Causa observada

- Los runs fallidos del workflow `Tests automatizados` del 2026-03-13 (`23030692404` y anteriores del mismo PR) no mostraban assertions ni tracebacks de tests.
- Tanto `smoke` como `pytest` terminaban con `exit code 137`.
- Localmente la suite pasaba tanto con:
  - `docker compose exec -T django pytest -m smoke`
  - `docker compose exec -T django pytest -n auto --cov=. --cov-report=term-missing --cov-fail-under=75`
  - `docker compose run --rm --no-deps django pytest -m smoke`
  - `docker compose run --rm --no-deps django pytest -n auto --cov=. --cov-report=term-missing --cov-fail-under=75`

La hipótesis adoptada es que el patrón `docker compose up` + `docker compose exec` hacía correr `pytest` dentro del mismo contenedor `django` que ya estaba ejecutando `runserver`, aumentando consumo de memoria y terminando en `SIGKILL`/OOM en GitHub Actions.

## Cambio aplicado

- `smoke`:
  - deja de levantar el servicio `django` persistentemente;
  - corre `docker compose run --build --rm --no-deps -T django pytest -m smoke`.
- `pytest`:
  - deja de levantar el servicio `django` persistentemente;
  - corre `docker compose run --build --rm --no-deps -T django pytest -n auto --cov=. --cov-report=term-missing --cov-fail-under=75`.
- Se explicita `USE_SQLITE_FOR_TESTS=1` en el `.env` de CI para que el workflow refleje el comportamiento real de tests del repo.

## Impacto

- Reduce el estado y procesos residentes durante los jobs de tests.
- Hace explícito que `smoke` y `pytest` usan SQLite en tests.
- Mantiene `migrations_check` como job separado con MySQL real para validar consistencia de migraciones.
