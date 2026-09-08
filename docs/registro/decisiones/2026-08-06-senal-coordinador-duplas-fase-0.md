# 2026-08-06 - Señal de coordinador de Duplas

## Contexto

La señal sobre `Profile.duplas_asignadas` estaba declarada en `users.signals`
e importaba `Dupla` para mantener el campo `Dupla.coordinador`.

## Decision

El receiver se traslada a `duplas.signals`, donde ya vive la sincronizacion
inversa de la misma relación. Se mantiene el mismo sender y los casos
`post_add`, `post_remove` y `post_clear`.

## Consecuencias

- `users` deja de importar el modelo de Duplas.
- La relación bidireccional conserva sus actualizaciones y limpiezas actuales.
- Se retira una excepción runtime de `.importlinter`.

## Validacion

- `black --check users/signals.py duplas/signals.py duplas/test_profile_duplas_signal.py tests/test_users_signals_unit.py`.
- `pytest tests/test_users_signals_unit.py duplas/test_profile_duplas_signal.py -q`.
- `python manage.py check`.
- `lint-imports`.
