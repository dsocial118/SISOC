# Filtro de listado de usuarios por alcance delegable

## Fecha
2026-03-29

## Cambio
Se agrego filtrado en el listado de usuarios para actores con alcance de delegacion configurado.

## Regla aplicada
Si el usuario logueado tiene `Profile.grupos_asignables` y/o `Profile.roles_asignables` (solo `auth.role_*`), el listado en `/usuarios/` muestra unicamente usuarios cuyos:
- grupos sean subconjunto de `grupos_asignables`, y
- roles directos (`auth.role_*`) sean subconjunto de `roles_asignables`.

Ademas, el usuario actor siempre se visualiza a si mismo en el listado.

Si el actor no tiene alcance configurado, se mantiene el comportamiento anterior (sin recorte adicional).

## Archivos
- `users/services.py`
- `users/tests.py`

## Validacion
- `docker compose exec -T django pytest users/tests.py -q` -> 4 passed
- `docker compose exec -T django python manage.py check` -> sin issues
