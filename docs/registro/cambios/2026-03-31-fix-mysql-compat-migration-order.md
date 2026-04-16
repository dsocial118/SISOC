# Fix MySQL compat en migración VAT 0021

## Contexto

La suite `mysql_compat` fallaba al crear la base de tests sobre MySQL real.
El error aparecía durante la migración `VAT 0021` con:

- `OperationalError (1553): Cannot drop index ... needed in a foreign key constraint`

## Cambio aplicado

- Se ajustó `VAT/migrations/0021_invert_titulo_plan_relation.py` para eliminar primero las `FOREIGN KEY` que usan `titulo_referencia_id` y recién después los índices/constraints `UNIQUE` asociados a esa columna.
- Se agregó un test de regresión en `VAT/tests.py` para asegurar ese orden de borrado.

## Decisión

Se mantuvo el enfoque de migración manual existente y se corrigió únicamente el orden de borrado requerido por MySQL, evitando cambios más amplios en la estructura o en los workflows de CI.

## Validación

- `docker compose run --rm --no-deps -T -e USE_SQLITE_FOR_TESTS=1 django pytest VAT/tests.py -k migracion_0021 -q`
- `docker compose up -d --build` + espera de MySQL + `docker compose exec -T django pytest tests/test_mysql_compatibility.py::test_mysql_backend_activo_en_suite_mysql_compat tests/test_mysql_compatibility.py::test_mysql_integridad_unicidad_username_con_rollback -q -vv`
