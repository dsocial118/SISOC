# 2026-08-06 - Registro post-fixture para Intervenciones

## Contexto

El comando transversal `load_fixtures` en `core` importaba y ejecutaba
directamente la sincronizacion del catálogo de Intervenciones después de
cargar los fixtures.

## Decision

`core.services.fixture_post_load` expone un registro ordenado por nombre e
idempotente de callbacks. Intervenciones registra su sincronizacion de catálogo desde
`AppConfig.ready()` y conserva el mismo mensaje operativo del comando.

## Consecuencias

- El comando mantiene la orquestacion de fixtures y la sincronizacion territorial de `core`.
- Intervenciones conserva la propiedad de su catálogo y de su post-proceso.
- No se ejecutan callbacks al registrar las apps.
- Se retira una excepcion runtime de `.importlinter`.

## Validacion

- `black --check core/services/fixture_post_load.py intervenciones/fixture_post_load.py intervenciones/apps.py core/management/commands/load_fixtures.py tests/test_load_fixtures_command.py tests/test_fixture_post_load_registry_unit.py intervenciones/tests/test_fixture_post_load.py`.
- `pytest tests/test_load_fixtures_command.py tests/test_fixture_post_load_registry_unit.py intervenciones/tests/test_services_catalogo.py intervenciones/tests/test_fixture_post_load.py -q`.
- `python manage.py check`.
- `lint-imports`.
