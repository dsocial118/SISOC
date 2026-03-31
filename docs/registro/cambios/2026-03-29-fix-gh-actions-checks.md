# 2026-03-29 - Correcciones para destrabar GitHub Actions en development

## Contexto

Luego de integrar cambios recientes en `development`, la validación de GitHub Actions quedó bloqueada por una combinación de problemas de sintaxis, formato, conflictos de migraciones y regresiones detectadas por la suite completa.

## Causa raíz

- `comedores/tests.py` quedó con un test truncado, lo que rompía la recolección de `pytest`.
- Había archivos Python y templates fuera de formato respecto de `black` y `djlint`.
- `comedores` tenía dos hojas de migración activas sin un merge común y además faltaban migraciones de `RenameIndex` detectadas por Django en `comedores` y `users`.
- `ComedorService._consultar_renaper_por_dni` había perdido el comportamiento fail-fast ante errores de integración y volvía a probar los tres sexos.
- `ComedorDetailView` asumía siempre la relación `colaboradores_espacio`, lo que rompía tests unitarios que usan dobles livianos.
- Algunos tests seguían afirmando comportamiento viejo ya documentado en relevamientos y Celiaquía.

## Cambios aplicados

- Se reparó la sintaxis de `comedores/tests.py` y se alineó el test legacy del detalle de comedor con el redireccionamiento actual a `relevamientos`.
- Se reformatearon los archivos que bloqueaban `black` y `djlint`.
- Se agregó `comedores/migrations/0033_merge_20260329_1458.py` para unificar ramas de migración y se incorporaron las migraciones generadas de rename de índices en `comedores` y `users`.
- Se restauró el corte temprano en `_consultar_renaper_por_dni` cuando RENAPER falla por integración y no por “sin coincidencia”.
- Se hizo defensivo `ComedorDetailView._build_relaciones_relevamiento_base_context` para tolerar objetos sin manager `colaboradores_espacio` en tests unitarios.
- Se ajustó un test de Celiaquía para respetar el comportamiento vigente: ante validación fallida se conserva `datos_raw` previo y se actualiza el error.

## Validación ejecutada

- `docker compose run --build --rm --no-deps -T django black --check . --config pyproject.toml`
- `docker compose run --build --rm --no-deps -T django djlint . --check --configuration=.djlintrc`
- `docker compose run --build --rm --no-deps -T django pytest -m smoke`
- `docker compose exec -T django python manage.py makemigrations --check --dry-run`
- `docker compose exec -T django pytest -m mysql_compat -q`
- `docker compose run --build --rm --no-deps -T django pytest -n auto --cov=. --cov-report=term-missing --cov-fail-under=75`

## Impacto esperado

- Se destraban los jobs de formato, smoke, migraciones, compatibilidad MySQL y suite completa de tests.
- No se cambian contratos públicos nuevos; se corrigen regresiones y se sincroniza el estado del repositorio con lo que la CI ya exige.
