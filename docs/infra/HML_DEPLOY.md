# HML - Deploy

Estado: documentado; no se ejecuto deploy ni restart durante la auditoria.

## Flujo vigente

1. Un push o dispatch a `homologacion` dispara `.github/workflows/deploy.yml`.
2. El job usa el runner self-hosted `sisoc-homologacion` en `hml-old`.
3. GitHub Environment `homologacion` aporta `APP_ROOT`.
4. `scripts/operacion/deploy_refresh.sh` valida entorno, branch y Compose.
5. Ejecuta fetch, validacion Compose, `down`, pull `--ff-only`, build/up y `ps`.
6. Despliega tambien `/sisoc/SISOC-Mobile` desde branch `main`; su origin
   publico conocido se normaliza de SSH a HTTPS antes del fetch.
7. El entrypoint backend puede ejecutar migraciones y otros comandos con
   escritura en DB antes de iniciar Gunicorn.

Cuando cambia `main`, el Plan A abre/integra un PR descendente hacia
`homologacion` si no hay conflictos y solicita este deploy explicitamente. Los
cambios exclusivos de HML se conservan y nunca se copian hacia `main` por ese
flujo.

## Checklist previo

- [ ] Cambio aprobado para HML.
- [ ] Commits objetivo backend/mobile registrados.
- [ ] Backend en `homologacion` y mobile en `main`, ambos sin cambios tracked.
- [ ] Backup DB vigente confirmado si el cambio puede modificar datos/schema.
- [ ] Backup de configuracion creado con `backup_hml_configs.sh`.
- [ ] Espacio libre suficiente para reconstruir ambos stacks.
- [ ] Responsable, ventana y rollback disponibles.

## Comandos seguros previos

```bash
git -C /sisoc/SISOC status --short --branch
git -C /sisoc/SISOC-Mobile status --short --branch
/home/sisoc-deploy/bin/show_hml_status.sh
/home/sisoc-deploy/bin/backup_hml_configs.sh
```

## Wrappers manuales

Sin flags solo muestran el plan:

```bash
bash scripts/infra/deploy_hml.sh
bash scripts/infra/restart_hml.sh
```

La ejecucion real requiere aprobacion explicita del deploy/restart y de las
escrituras DB del entrypoint:

```bash
bash scripts/infra/deploy_hml.sh --apply --acknowledge-db-writes
bash scripts/infra/restart_hml.sh --apply --acknowledge-db-writes
```

`restart_hml.sh` omite pull, pero igualmente reconstruye backend/mobile y puede
escribir DB. Ninguno de estos comandos es un health check ni un rollback seguro.

## Verificacion posterior

```bash
bash scripts/infra/healthcheck_hml.sh
docker compose -f /sisoc/SISOC/docker-compose.deploy.yml ps
docker compose -f /sisoc/SISOC-Mobile/compose.prod.yaml ps
git -C /sisoc/SISOC rev-parse HEAD
git -C /sisoc/SISOC-Mobile rev-parse HEAD
df -h /
```

Agregar una prueba funcional autorizada con lectura DB. El certificado vencido
es un riesgo separado y no debe ocultar fallas nuevas del deploy.

## Rollback de deploy

Registrar los commits e imagenes previos antes de aplicar. No ejecutar otro
deploy improvisado: reconstruye stacks y puede escribir DB. Si el cambio falla,
aprobar el commit de retorno, revisar compatibilidad de schema/datos, restaurar
DB solo desde un backup validado cuando corresponda y repetir la verificacion.
