# Implementacion del Plan A

## Alcance

1. Agregar `.github/workflows/sync-main-downstream.yml`.
2. Agregar `workflow_dispatch` a `.github/workflows/deploy.yml`.
3. Hacer que `scripts/operacion/deploy_refresh.sh` use el remote HTTPS publico
   conocido de SISOC-Mobile y rechace origins inesperados.
4. Actualizar la documentacion operativa de deploy y riesgos de HML/QA.
5. Validar sintaxis YAML y Bash, mas escenarios focalizados del remote mobile.
6. Publicar un PR enfocado hacia `main` y esperar sus checks.
7. Una vez integrado, comprobar que la sincronizacion incorpora `main` en
   `development` y `homologacion` y que ambos deploys finalizan correctamente.

## Criterios de aceptacion

- `git merge-base --is-ancestor origin/main origin/development` devuelve 0.
- `git merge-base --is-ancestor origin/main origin/homologacion` devuelve 0.
- Los extras de `development`/`homologacion` no aparecen en `main` por este flujo.
- El workflow no usa force push ni credenciales persistentes nuevas.
- Un conflicto bloquea el deploy de la rama afectada.
- QA y HML pueden actualizar SISOC-Mobile sin clave SSH del servidor.
- Los deploys no interactivos mantienen validacion de branch, working tree y
  configuracion Compose.

## Validacion focalizada

```bash
bash -n scripts/operacion/deploy_refresh.sh
python -c "import pathlib, yaml; [yaml.safe_load(pathlib.Path(p).read_text()) for p in ['.github/workflows/deploy.yml', '.github/workflows/sync-main-downstream.yml']]"
```

Ademas se ejecutara una prueba aislada con repositorios Git temporales para
confirmar que se acepta el origin SSH/HTTPS esperado, se normaliza a HTTPS y se
rechaza un origin ajeno sin ejecutar Docker.

## Fuera de alcance

- aprobar el Environment de produccion;
- desplegar o reiniciar PRD;
- resolver automaticamente conflictos entre ramas;
- modificar `.env`, owners, permisos o servicios de los servidores;
- renovar TLS.
