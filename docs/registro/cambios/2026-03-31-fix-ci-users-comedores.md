# 2026-03-31 - Fix CI users y comedores

## Contexto

Se saneó el branch para destrabar checks de CI que estaban fallando en cascada por:

- errores de sintaxis en `users`
- árbol de migraciones inconsistente en `users` y `comedores`
- template roto en `templates/includes/sidebar/opciones.html`
- expectativas desactualizadas en tests de `users` y `comedores`
- cadenas con mojibake en mensajes/API que disparaban `encoding_check`

## Cambios aplicados

- Se corrigieron los errores de sintaxis en `users/services.py` y `users/views.py`.
- Se ordenó el árbol de migraciones de `users` y `comedores` para evitar columnas e índices duplicados.
- Se restauró una versión sana de `templates/includes/sidebar/opciones.html` y se reformateó con `djlint`.
- Se alinearon tests de `users` con el comportamiento vigente de permisos y render.
- Se alineó `tests/test_comedores_api_views_unit.py` con el flujo PWA real de `ComedorDetailViewSet.list`.
- Se corrigieron mensajes con mojibake en `users/views.py` y `comedores/api_views.py`.
- Se refactorizó la carga de comprobantes en `comedores/api_views.py` para evitar mutar `request._full_data`.

## Validación ejecutada

- `docker compose exec django black --check users/views.py users/services.py tests/test_users_auth_flows.py --config pyproject.toml`
- `docker compose exec django djlint templates/includes/sidebar/opciones.html --check --configuration=.djlintrc`
- `docker compose exec django python manage.py makemigrations --check --dry-run`
- `docker compose exec django pylint users/views.py users/services.py tests/test_users_auth_flows.py --rcfile=.pylintrc`
- `docker compose exec django black --check comedores/api_views.py tests/test_comedores_api_views_unit.py --config pyproject.toml`
- `docker compose exec django pylint comedores/api_views.py tests/test_comedores_api_views_unit.py --rcfile=.pylintrc`
- `docker compose exec django pytest tests/test_users_auth_flows.py -q`
- `docker compose exec django pytest tests/test_comedores_api_views_unit.py tests/test_pwa_comedores_api.py -q`
- `docker compose exec django pytest -m mysql_compat -q`
- `docker compose exec django pytest -m smoke`
- `docker compose exec django pytest -n auto`

## Resultado

Quedó validado localmente:

- `1627 passed`
- `1 skipped`
- `3 warnings` esperables por `logout` vía GET en Django
