# 2026-07-13 - Retiro Stage 1 del MySQL local de QA

## Contexto

Django fue comprobado contra `10.80.9.18` (`ltestsql-ssies`). El MySQL local en
`qa-old` era un clon de 43 GB con el mismo `server_uuid`, activo y expuesto en
3306 aunque no formaba parte de la arquitectura vigente.

## Cambios aplicados

- Preflight: cero clientes inesperados, eventos, replicas o Group Replication.
- Backup root-only en
  `/var/backups/sisoc/mysql-local-retirement/20260713_115645`.
- `mysql.service` detenido y deshabilitado.
- `/var/lib/mysql` y paquetes MySQL conservados intactos.
- Ventana de observacion hasta 2026-07-20.

## Impacto esperado

- El host de aplicacion deja de exponer un MySQL heredado.
- El espacio no cambia todavia porque Stage 1 prioriza rollback inmediato.
- Django continua usando la DB canonica separada.

## Validacion

- `mysql.service`: `inactive` y `disabled`.
- cero procesos `mysqld` y cero listeners locales en 3306.
- Django continuo conectado a `10.80.9.18`.
- `/` y `/health/`: HTTP 200.
- Docker, containerd, NGINX, cron y runner activos.
- DB remota `10.80.9.18:3306` alcanzable.

## Riesgos y rollback

Los 43 GB todavia requieren decision de conservacion antes de Stage 2. Rollback:

```bash
sudo systemctl enable --now mysql
```

No se requiere reiniciar Django para restaurar el servicio local.
