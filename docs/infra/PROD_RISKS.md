# Produccion - Riesgos de infraestructura

Estado: auditoria read-only del 2026-07-13. Ninguna recomendacion de este
documento autoriza cambios en produccion.

## Riesgos criticos

### 1. Backups y restores de DB/media no demostrados

La DB canonica vive en `10.80.5.46` y media ocupa 65 GiB/68,455 archivos. No se
obtuvo evidencia de backup vigente ni restore probado para ninguno.

Impacto: perdida de datos, migracion incompleta o imposibilidad de rollback.

### 2. Certificado TLS vencido

El wildcard vencio el 2026-03-06 y clientes estrictos rechazan HTTPS. El riesgo
queda registrado, pero su tratamiento fue postergado explicitamente por el
responsable. No se propone ni ejecuta ningun cambio TLS en esta fase.

### 3. Cron root combina runtime vigente con paths historicos

Root tiene cuatro entradas que coinciden por familia con `scripts/crontab`:
HetrixTools, poda Docker, limpieza en un path `/home/admin-ssies` inexistente y
`purge_auditlog` desde un path `/opt/ssies` inexistente. El contrato versionado
incluye `docker system prune` con 24h y `--volumes`.

Impacto: tareas silenciosamente fallidas, retencion de auditoria no confiable y
posible eliminacion automatica de recursos Docker utiles. La opcion exacta de la
linea efectiva debe confirmarse antes de proponer edicion.

### 4. MySQL local activo y expuesto sin uso observado

Django usa `10.80.5.46`, pero el app host escucha en `0.0.0.0:3306`. El local
tiene 200 MB, cero schemas de aplicacion, clientes reales, eventos o replicacion.

Impacto: superficie de red, mantenimiento innecesario y riesgo de confundirlo
con la DB canonica. En produccion no se detiene; solo se propone un Stage 1
reversible futuro.

## Riesgos altos/medios

- NGINX access log ocupa ~1.90 GB y error log ~116 MB, fuera de las rutas
  logrotate detectadas; los logs Django agregan 1.3 GB.
- No hay politica demostrada de backup/retencion para configuracion, cron y
  runner.
- El workflow de produccion no despliega SISOC-Mobile, a diferencia de HML; un
  deploy backend puede dejar versiones no coordinadas.
- Gunicorn queda publicado en todas las interfaces por 8001, permitiendo bypass
  de NGINX/TLS si la red lo alcanza.
- `.env` mobile es `root:root` modo 664: es world-readable y el owner/grupo no
  reflejan al runner `sisoc-deploy`.
- Los logs NGINX son modo 644 y pueden incluir URLs, parametros o identificadores
  sensibles legibles por usuarios locales.
- `/var/www/SISOC` conserva modo 777 y un checkout historico.
- `apache2` y `sisoc.service` estan habilitados/fallidos; el segundo apunta a un
  path inexistente.
- Puertos 10000/10050 estan expuestos globalmente; corresponden a Webmin/Zabbix,
  pero ACL/firewall no fueron verificados.
- Listener 556 en localhost sin owner confirmado.
- `tmp/` backend tiene tres archivos no trackeados; no se leyo contenido ni se
  confirmo ciclo de vida.
- Cuatro workers fueron recreados horas despues del resto del stack; puede ser
  normal, pero el flujo no esta documentado.

## Riesgos bajos

- Hay 25 imagenes Docker no activas, pero solo consumen ~5 GB y el disco tiene
  663 GB libres; no justifican una limpieza manual.
- Un volumen `frontend_node_modules` de 210 MB esta inactivo; es regenerable,
  pero no se borra sin confirmar el flujo mobile.
- Versiones/runtime difieren de QA; no deben igualarse por estetica.
- NGINX reutiliza paths historicos bajo `/etc/apache2/certs`.

## Seguridad

1. TLS vencido, postergado.
2. MySQL local y Gunicorn expuestos en todas las interfaces.
3. `.env` mobile y logs NGINX con lectura global.
4. Checkout historico modo 777.
5. Webmin/Zabbix expuestos sin ACL efectiva verificada.
6. Runner self-hosted con capacidad de desplegar produccion.

## Mantenibilidad

- Dos repos y dos stacks con deploy no simetrico.
- Cron efectivo mezcla paths vigentes e inexistentes.
- Servicios legacy habilitados/fallidos alrededor del runtime real.
- Logs voluminosos fuera de una politica de rotacion confirmada.
- Deploy/restart backend puede escribir DB por el entrypoint.
- No hay runbook productivo versionado que cierre backup, mobile y restore.

## Migrabilidad

- Media 65 GiB sin copia verificada.
- DB externa sin restore probado.
- Secretos backend/mobile deben transferirse por canal seguro.
- NGINX, runner, cron, monitoreo y DNS/TLS deben recrearse.
- Workers especializados y mobile deben incluirse en el cutover.
- Checkouts historicos, logs, caches e imagenes no deben copiarse por defecto.

## Seguro realizar ahora

1. Mantener y revisar estos documentos.
2. Monitorear disco, health, listeners y tamanios en modo read-only.
3. Obtener evidencia externa de backups/restores sin tocar la DB.
4. Confirmar linea exacta de cron root mediante un conteo sanitizado.
5. Clasificar owners de puertos y responsables operativos.

## Requiere aprobacion explicita

- editar cron o instalar tareas nuevas;
- detener/deshabilitar/purgar MySQL local;
- editar/reload NGINX o logrotate;
- cambiar permisos/owners;
- deshabilitar Apache, `sisoc.service`, Webmin o Zabbix;
- cambiar Compose, binds o workflow de deploy;
- deploy, restart, pull, migraciones o cambios DB;
- mover/borrar media, logs, `tmp/`, volumenes, imagenes o checkouts;
- copiar secretos o backups sensibles.

## No conviene tocar todavia

1. DB, media y logs hasta tener backup/retencion/restore acordados.
2. MySQL local hasta una ventana, backup root-only y observacion aprobados.
3. Cron root hasta leer la linea exacta y validar ownership funcional.
4. Deploy mobile hasta probar rollback y compatibilidad con `main`.
5. Paths/permisos legacy hasta clasificar contenido y dependencias.
6. TLS por instruccion expresa del responsable.
