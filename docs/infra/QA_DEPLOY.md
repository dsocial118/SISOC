# QA - Deploy

Estado: documentado; no se ejecuto deploy ni restart durante la auditoria.

## Flujo vigente

1. Un push a `development` dispara `.github/workflows/deploy.yml`.
2. El job usa el runner self-hosted `sisoc-qa` en `qa-old`.
3. GitHub Environment `qa` aporta `APP_ROOT`.
4. `scripts/operacion/deploy_refresh.sh` valida entorno, branch y Compose.
5. Ejecuta fetch, validacion Compose, `compose down`, pull `--ff-only`, build/up
   y `ps`.
6. El entrypoint ejecuta migraciones y comandos con escritura en DB antes de
   iniciar Gunicorn.

## Checklist previo

- [ ] Cambio aprobado para QA.
- [ ] Branch `development` y commit objetivo registrados.
- [ ] Working tree remoto revisado; la excepcion preexistente de cuatro ESC no se
      debe borrar sin aprobacion.
- [ ] Backup DB vigente confirmado si el cambio puede migrar datos/schema.
- [ ] Backup de configuracion creado con `backup_qa_configs.sh`.
- [ ] Espacio libre suficiente para build.
- [ ] Responsable y ventana disponibles para rollback.

## Comandos seguros previos

```bash
git -C /home/admin-ssies/sisoc-comedores-test/BACKOFFICE status --short --branch
/home/sisoc-deploy/bin/show_qa_status.sh
/home/sisoc-deploy/bin/backup_qa_configs.sh
```

## Ejecucion manual

El wrapper no cambia nada sin flags:

```bash
bash scripts/infra/deploy_qa.sh
```

La ejecucion real requiere aprobacion explicita de deploy y de escrituras DB:

```bash
bash scripts/infra/deploy_qa.sh --apply --acknowledge-db-writes
```

No ejecutar este comando como parte de una auditoria o health check.

## Verificacion posterior

```bash
/home/sisoc-deploy/bin/healthcheck_qa.sh
docker compose -f docker-compose.deploy.yml ps
git rev-parse HEAD
df -h /
```

Agregar una prueba funcional autorizada que consulte DB; `/health/` por si solo
no confirma conectividad de datos.
