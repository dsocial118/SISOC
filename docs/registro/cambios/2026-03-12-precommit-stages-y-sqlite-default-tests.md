# 2026-03-12 - Hooks por etapa y SQLite por defecto en tests

## Resumen

Se reorganizó `pre-commit` para separar checks rápidos y pesados:
- `pre-commit`: hooks de formato/higiene/secretos.
- `pre-push`: `pylint` global y `pytest -m smoke`.

También se ajustó la configuración de Django para usar SQLite por defecto en tests.

## Detalle técnico

- Archivo modificado: `.pre-commit-config.yaml`
  - `default_install_hook_types`: `pre-commit`, `pre-push`.
  - `pre-commit`: `gitleaks`, `black`, `check-yaml`, `end-of-file-fixer`, `trailing-whitespace`, `detect-private-key`.
  - `pre-push`: `pylint` global y smoke tests en Docker.
- Archivo modificado: `config/settings.py`
  - `USE_SQLITE_FOR_TESTS` ahora usa `_safe_bool_env(..., True)` (default verdadero).
- Archivo modificado: `.env.example`
  - `USE_SQLITE_FOR_TESTS=1`.

## Impacto

- Commits más ágiles con controles rápidos.
- Pushes con barrera de calidad adicional antes de llegar a CI.
- Tests locales más simples por default al usar SQLite.
