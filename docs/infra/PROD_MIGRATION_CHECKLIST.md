# Produccion - Checklist de migracion

Fuente canonica actual: `prd-old` (`10.80.5.45`). Los hosts AWS son referencias
de una posible migracion y no forman parte del runtime vigente.

Este checklist no autoriza nuevos cutovers, deploys, backups, restores ni
cambios. El backup local de media ya ejecutado tuvo aprobacion separada.

## Gobierno previo

- [ ] Definir responsables de aplicacion, DB, red/DNS, TLS y backups.
- [ ] Aprobar ventana, comunicaciones, criterio go/no-go y rollback.
- [ ] Congelar cambios o registrar commits exactos durante el cutover.
- [ ] Confirmar que HML valido la misma version y el flujo mobile.
- [ ] Definir RTO/RPO y tiempo maximo de indisponibilidad.

## Registrar fuente

- [x] Host app: `prd-old` / `10.80.5.45` / `mdsldmz-ssies`.
- [x] Backend: `/sisoc/SISOC`, branch `main`, commit auditado
      `980c2b05397b3a18bdcd5853763c6942632232ed`.
- [x] Mobile: `/sisoc/SISOC-Mobile`, branch `main`, commit auditado
      `ec7c163fede8b3877fff0fd7863f0a7812043c2c`.
- [x] DB real: `10.80.5.46:3306`, servidor `ldmzsql-sisoc`, schema
      `sisoc_local`.
- [x] Media: 65 GiB, 68,548 archivos al tomar el backup local.
- [x] Servicios activos: siete contenedores, NGINX, runner, Zabbix y Webmin.
- [ ] Repetir HEAD/conteos inmediatamente antes del cutover.

## Respaldar y copiar

- [ ] Verificar ubicacion, retencion e integridad de los backups DB informados y
      probar restore aislado de `10.80.5.46`.
- [x] Crear copia local de `/sisoc/SISOC/media` preservando metadata en
      `/sisoc/backups/media/20260713_172352/media`; dos pasadas y cero
      diferencias pendientes.
- [ ] Copiar media fuera de `prd-old` y verificar checksums antes del cutover.
- [ ] Transferir `.env` backend/mobile por canal seguro, sin imprimir valores.
- [ ] Exportar configuracion NGINX, metadata TLS, systemd/runner y cron efectivo.
- [ ] Guardar commits, Compose, Dockerfiles y scripts operativos versionados.
- [ ] Definir si logs deben copiarse por requisito legal/forense; no moverlos por
      defecto.
- [ ] Guardar inventario de owners/permisos sin replicar modos inseguros a ciegas.

No usar como fuente primaria:

- MySQL local del app host;
- `/var/www/SISOC` o `/opt/ssies/SISOC-Backoffice-deprecated`;
- `static_root/`, imagenes o build cache Docker regenerables;
- `node_modules` o el volumen `frontend_node_modules`;
- `tmp/` sin clasificar;
- credenciales persistentes del runner;
- dumps antiguos no validados.

## Reinstalar/configurar

- [ ] SO soportado, Git, Docker Engine y Compose compatibles.
- [ ] Usuario `sisoc-deploy`, grupos minimos y acceso SSH auditado.
- [ ] Backend/OCR/workers desde un checkout limpio del commit aprobado.
- [ ] SISOC-Mobile desde un checkout limpio del commit aprobado.
- [ ] NGINX con 80/443, redirects, static/media, backend y `/mobile/`.
- [ ] DB separada con ACL, backup, retencion y monitoreo.
- [ ] Runner nuevo con label `sisoc-produccion`; no copiar su identidad anterior.
- [ ] GitHub Environment `production`, `APP_ROOT` y reviewers requeridos.
- [ ] Zabbix/Webmin/HetrixTools solo si tienen owner y necesidad confirmados.
- [ ] Logrotate, monitoreo de disco/media y alertas de health.
- [ ] DNS/TLS y mecanismo autoritativo de renovacion, aunque TLS quede fuera del
      orden actual.

No igualar versiones a QA/HML por estetica. Mantener compatibilidad con las
imagenes y configuraciones probadas o cambiar versiones mediante un proyecto
separado.

## Secretos a recrear por canal seguro

- Django secret, hosts/origins y configuracion de runtime.
- Credenciales MySQL.
- GESTIONAR y RENAPER.
- Correo, Sentry y Ticketera.
- Configuracion no publica de SISOC-Mobile.
- Token efimero de registro del runner/deploy keys.
- Clave TLS solo si la politica aprueba transferirla.

Nunca versionar `.env`, copiarlo a reportes ni incluir valores en logs de CI.

## Orden de construccion del destino

1. red, firewall, storage y usuarios;
2. DB restaurada y validada en aislamiento;
3. Docker/containerd;
4. backend Django y cinco workers, con escrituras del entrypoint aprobadas;
5. SISOC-Mobile;
6. NGINX/DNS/TLS;
7. cron, logrotate, Zabbix/Webmin/HetrixTools;
8. runner self-hosted, despues de validar manualmente el runtime.

## Cutover

- [ ] Tomar backup final y delta final de media.
- [ ] Registrar commit backend/mobile y estado Git limpio.
- [ ] Autorizar side effects del entrypoint antes del primer `up`.
- [ ] Levantar los siete servicios Compose y verificar restart policies.
- [ ] Validar DB remota desde Django con una consulta read-only.
- [ ] Cambiar trafico/DNS solo despues del health interno.
- [ ] Mantener `prd-old` sin cambios y disponible para rollback.

## Validacion de exito

```bash
hostnamectl
df -hT /
df -ih /
systemctl is-active docker containerd nginx cron
docker compose -f /sisoc/SISOC/docker-compose.deploy.yml \
  -f /sisoc/SISOC/docker-compose.produccion.yml ps
docker compose -f /sisoc/SISOC-Mobile/compose.prod.yaml ps
git -C /sisoc/SISOC rev-parse HEAD
git -C /sisoc/SISOC-Mobile rev-parse HEAD
ss -lntup
curl --max-time 8 -fsS https://sisoc.secretarianaf.gob.ar/health/
curl --max-time 8 -fsS https://sisoc.secretarianaf.gob.ar/mobile/
```

Ademas:

- [ ] login y pagina con datos mediante usuario autorizado;
- [ ] worker OCR estable sin disparar un job real no aprobado;
- [ ] workers de mailing/importacion activos, sin reprocesar tareas;
- [ ] static y un media existente;
- [ ] conteo/checksum de media;
- [ ] logs sin errores nuevos, revisados localmente sin copiar PII;
- [ ] runner/cron/monitoreo activos;
- [ ] backup y restore documentados.

## Detectar fallo

- health no 200 o DB identity distinta;
- contenedor reiniciando/unhealthy;
- worker ausente o cola reprocesando inesperadamente;
- static/media 404 o checksums distintos;
- errores nuevos en NGINX/Django;
- latencia/tasa de error fuera del baseline;
- disco/inodos creciendo anormalmente;
- commit o branch distinto del aprobado.

## Rollback

- [ ] Devolver trafico/DNS a `prd-old`.
- [ ] Detener el destino sin tocar la fuente.
- [ ] No restaurar parcialmente sobre DB fuente sin plan aprobado.
- [ ] Preservar logs/evidencia del intento.
- [ ] Confirmar health, DB, workers y mobile en `prd-old`.
- [ ] Reabrir cutover solo despues de identificar la causa.
