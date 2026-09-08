# 2026-08-06 - Pruebas de alcance territorial en Ciudadanos

## Contexto

`users/tests.py` contenía pruebas de alcance territorial que creaban y
consultaban `Ciudadano`, además de varias regresiones PWA que usan modelos de
Comedores y Organizaciones. La excepción de import-linter permitía cualquier
import de dominio desde las pruebas de Users.

## Decision

Las dos pruebas que ejercitan el queryset de Ciudadanos se trasladan a
`ciudadanos/test_territorial_scope.py` con helpers locales. El módulo heredado
restante se mueve a `tests/test_users_regressions.py`, donde pytest mantiene su
descubrimiento sin convertir los imports de dominio en dependencias de `users`.

## Consecuencias

- No cambia código de producción ni el contrato de alcance territorial.
- El paquete `users` deja de contener un módulo de tests que importe apps de dominio.
- Se retira una excepción de tests de `.importlinter`.

## Validacion

- `black --check tests/test_users_regressions.py ciudadanos/test_territorial_scope.py`.
- `pytest tests/test_users_regressions.py ciudadanos/test_territorial_scope.py -q`.
- `python manage.py check`.
- `lint-imports`.
