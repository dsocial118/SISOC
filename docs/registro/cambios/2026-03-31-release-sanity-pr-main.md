# Release sanity para PRs a main

## Contexto

Los workflows existentes validaban lint, tests, migraciones, secretos y documentacion automatica, pero no ejecutaban una verificacion especifica del escenario de release antes de mergear a `main`.

## Cambio realizado

- Se agrego el workflow `.github/workflows/release-sanity.yml`.
- El nuevo workflow corre solo en pull requests hacia `main`.
- Valida `python manage.py check --deploy` con `ENVIRONMENT=prd`.
- Valida la generacion del schema OpenAPI con `python manage.py spectacular --validate`.
- Valida `python manage.py collectstatic --noinput`.
- Se actualizo `deploy_guard` para exigir `release_sanity` solo cuando el PR apunta a `main`.

## Objetivo

Detectar antes del merge errores de configuracion de despliegue, rupturas en el schema OpenAPI y problemas de estaticos que pueden no aparecer en la suite de tests general.
