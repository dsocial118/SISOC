# 2026-05-11 - Script operativo de deploy refresh

## Cambio

Se agrego `scripts/operacion/deploy_refresh.sh` para automatizar el flujo manual de despliegue en servidores:

1. leer `ENVIRONMENT` desde `.env`;
2. elegir los compose files correctos para el entorno;
3. validar la branch esperada y el compose;
4. ejecutar `docker compose down --remove-orphans`;
5. actualizar la branch actual con `git pull --ff-only`;
6. levantar el stack con `docker compose up -d --build`;
7. mostrar el estado con `docker compose ps`.

Tambien se agrego el argumento `--with-mobile` para desplegar `SISOC-Mobile` desde el checkout hermano `../SISOC-Mobile` o desde la ruta indicada con `--mobile-dir`.

## Decision

El script mantiene el contrato actual del repo:

- `dev|local|development` usa `docker-compose.yml`;
- `qa|homologacion` usa `docker-compose.deploy.yml`;
- `prd|prod|production` usa `docker-compose.deploy.yml` + `docker-compose.produccion.yml`.

Cuando se usa `--with-mobile`, el script de SISOC delega el deploy mobile ejecutando `bash <SISOC-Mobile>/scripts/operacion/deploy_refresh.sh`. Las opciones compatibles se reenvian al script mobile para que cada repo conserve su propia logica operativa.

No borra volumenes por defecto. La opcion `--volumes` existe, pero exige confirmacion salvo que se use `--yes`, porque en entornos locales puede eliminar datos persistentes.

## Validacion

- `bash -n scripts/operacion/deploy_refresh.sh`
- `ENV_FILE=<tmp-env> bash scripts/operacion/deploy_refresh.sh --dry-run --allow-branch-mismatch`
- `ENV_FILE=<tmp-env> bash scripts/operacion/deploy_refresh.sh --with-mobile --mobile-dir <sisoc-mobile> --dry-run --allow-branch-mismatch --allow-dirty`
- `docker compose -f docker-compose.deploy.yml config -q`
- `docker compose -f docker-compose.deploy.yml -f docker-compose.produccion.yml config -q`

## Riesgos

- El script asume que el checkout del servidor esta en la branch correcta para el entorno.
- Con `--with-mobile`, tambien asume que el checkout mobile esta disponible y es un repo Git valido.
- Si hay cambios tracked locales, falla por defecto para evitar mezclar deploy con ediciones manuales.
- `--volumes` debe usarse solo cuando se quiera destruir volumenes del stack.
