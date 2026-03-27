# 2026-03-27 - CI MySQL compatibility + default consistente de password age

## Contexto

Se detectaron dos hallazgos en el rango `stable-2026.03.18..development`:

- La CI ejecutaba tests con `USE_SQLITE_FOR_TESTS=1` en casi todos los jobs, sin un subset explícito que valide compatibilidad sobre MySQL real.
- `INITIAL_PASSWORD_MAX_AGE_HOURS` tenía valor `72` en `.env.example`, mientras que el default en código (`config/settings.py`) es `336`.

## Cambios aplicados

- Se agregó el marker `mysql_compat` en `pytest.ini`.
- Se creó `tests/test_mysql_compatibility.py` con pruebas mínimas de compatibilidad MySQL:
  - Verificación de backend activo (`connection.vendor == "mysql"`).
  - Verificación de integridad/rollback ante unicidad de `username`.
- Se agregó job `mysql_compat` en `.github/workflows/tests.yml`:
  - Usa `USE_SQLITE_FOR_TESTS=0`.
  - Levanta MySQL con `docker compose`.
  - Ejecuta solo `pytest -m mysql_compat -q`.
- Se mantuvo SQLite para optimizar la suite principal (`smoke` y `pytest`).
- Se alineó `.env.example` a `INITIAL_PASSWORD_MAX_AGE_HOURS=336`.

## Impacto

- Se conserva velocidad de CI para la mayoría de tests.
- Se incorpora una barrera explícita de compatibilidad MySQL en PRs.
- Se elimina ambigüedad de configuración entre `.env.example` y defaults de settings.
