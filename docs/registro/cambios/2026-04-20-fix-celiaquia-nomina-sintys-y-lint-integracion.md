# Fix de integración Celiaquía: nómina SINTyS, registros erróneos y lint

## Contexto

La branch integradora de los PRs 1580, 1584 y 1587 seguía con fallas en tests de Celiaquía y en checks de lint del PR.

## Qué se ajustó

- Se normalizó `fecha_nacimiento` en `LegajoService` para tolerar valores `date`, `datetime` y strings ISO al calcular la edad de un legajo.
- Se ajustó el template de detalle de expediente para que la marca textual `Apellido Responsable *` solo aparezca cuando el responsable es realmente obligatorio.
- Se expuso explícitamente `LegajoService` desde `celiaquia.services.legajo_service` para que `pylint` resuelva correctamente el import usado por `celiaquia.models`.
- Se aplicó `black` a los archivos del PR que todavía no estaban formateados y dejaban rojo el check global.

## Validación

- `docker compose run --build --rm --no-deps -T django sh -lc "black --check . --config pyproject.toml && pylint **/*.py --rcfile=.pylintrc"`
- `docker compose run --build --rm --no-deps -T django sh -lc "djlint celiaquia/templates/celiaquia/expediente_detail.html --check --configuration=.djlintrc && pytest celiaquia/tests/test_nomina_sintys_export.py celiaquia/tests/test_registros_erroneos_obligatorios.py -q"`
- `docker compose run --build --rm --no-deps -T django pytest tests/test_legajo_service_unit.py tests/test_expediente_service_unit.py celiaquia/tests/test_validation_errors.py tests/test_celiaquia_expediente_view_helpers_unit.py celiaquia/tests/test_expediente_detail.py celiaquia/tests/test_nomina_sintys_export.py celiaquia/tests/test_registros_erroneos_obligatorios.py -q`
