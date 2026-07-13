# HML - Riesgos iniciales de infraestructura

Estado: actualizado despues del mantenimiento Docker aprobado del 2026-07-13.

## Riesgos criticos

### 1. Certificado TLS vencido

El certificado wildcard configurado en NGINX vencio el 2026-03-06. HTTPS solo
respondio al omitir validacion; una verificacion normal fallo con `curl` codigo
60. Todas las copias leaf/fullchain locales son el mismo certificado Sectigo
vencido. La key coincide, pero no hay un leaf renovado disponible.

Certbot apt y snap tienen timers activos sin archivos `renewal` ni `live`; no
administran el wildcard configurado. Ejecutar `certbot renew` no resuelve este
incidente.

Impacto: navegadores, integraciones y clientes estrictos pueden rechazar HML;
ademas se pierde una validacion realista previa a produccion.

Accion propuesta: obtener de Infra un wildcard Sectigo renovado y su cadena,
validar SAN/fechas/key, crear backup root-only, instalar, ejecutar `nginx -t`,
recargar NGINX y verificar sin `-k`. Todo requiere aprobacion y los archivos
externos correctos.

### 2. Filesystem raiz mitigado de 93% a 88%

La poda conservadora recupero aproximadamente 5 GB: quedan 12 GB libres. El
consumo principal sigue siendo `/sisoc` (49 GB, casi todo media). Docker conserva
capas recientes por la retencion de 14 dias; no se tocaron volumenes.

Impacto: fallas de build, logs, uploads, MySQL o deploy y posible caida abrupta.

La recurrencia quedo instalada para `sisoc-deploy` con umbral 80%, retencion 14
dias y prohibicion de volumenes. Monitorear la primera ejecucion automatica y el
disco porque 88% sigue por encima del objetivo.

### 3. Media local de 48 GiB sin backup verificado

`/sisoc/SISOC/media` contiene 45,303 archivos y domina el disco. No es
regenerable y debe tratarse como dato de negocio.

Impacto: perdida de uploads o migracion incompleta; crecimiento del filesystem
hasta agotar capacidad.

Accion segura: medir crecimiento, definir backup externo con checksum y probar
restore. No limpiar media por antiguedad ni moverla sin aprobacion.

### 4. MySQL local retirado en Stage 1, con rollback conservado

Django usa `10.80.5.48`. El MySQL heredado del host HML quedo inactivo y
deshabilitado el 2026-07-13, sin listener 3306. El preflight confirmo cero
schemas de aplicacion, clientes reales, eventos, replica y Group Replication.

El datadir de 200 MB y los paquetes siguen intactos. Backup root-only:
`/var/backups/sisoc/mysql-local-retirement/hml/20260713_135622`.

Riesgo pendiente: un purge prematuro eliminaria el rollback por una ganancia de
espacio insignificante. Observar hasta al menos el 2026-07-20; cualquier purge o
borrado requiere una aprobacion separada.

### 5. Backups y restores no demostrados

No hay evidencia actual de backup/restore para la DB HML ni para media. El
entorno no esta listo para una migracion segura hasta cerrar ambos puntos.

### 6. Restart/deploy con escrituras automaticas en DB

El stack backend comparte el entrypoint de QA: un arranque puede ejecutar
migraciones, fixtures y otros comandos. No existe un restart completamente
inocuo.

## Riesgos medios

- El mantenimiento Docker semanal quedo instalado, pero su primera ejecucion
  automatica todavia no fue observada.
- `homologacion` diverge de `development` (13 commits HML-only y 5 dev-only), por
  lo que una promocion/merge requiere revisar historia y no un pull improvisado.
- El comentario inline de `DATABASE_HOST` dice PRD aunque la IP es la DB HML
  canonica; puede inducir cambios equivocados.
- Puerto 8001 expone Gunicorn directamente, permitiendo bypass de NGINX/TLS.
- Puertos 10000/10050 escuchan globalmente sin owner confirmado.
- `sisoc.service` esta habilitado/fallido y apunta a un directorio inexistente.
- Apache esta habilitado/fallido mientras NGINX usa certificados alojados bajo
  su arbol de configuracion.
- Certbot apt y snap coexisten sin una autoridad clara.
- `/var/www/SISOC` tiene modo 777 y un working tree historico muy sucio.
- El checkout deprecated bajo `/opt/ssies` tambien esta sucio y contiene CSV no
  trackeados. Pueden ser datos; no borrar.
- `.env` de SISOC-Mobile es root:root modo 644. Contiene configuracion publica
  observada, pero se debe confirmar que nunca incorpore secretos.
- Un `docker compose logs -f` corre como root desde hace diez dias sin owner
  operativo identificado.
- No se verificaron cron root ni firewall/ACL efectivos.

## Riesgos bajos

- Diferencias de paths, owners y versiones Docker/Compose frente a QA reducen la
  portabilidad del runbook.
- Los logs HML son mayores que QA, aunque todavia no dominan el disco.
- NGINX reutiliza paths llamados `apache2`, agregando acoplamiento historico.
- El frontend movil no tiene flujo de deploy/rollback documentado en esta fase.

## Problemas de seguridad

1. Certificado vencido.
2. Gunicorn escucha en todas las interfaces.
3. Directorio historico `/var/www/SISOC` modo 777.
4. Puertos 10000/10050 sin clasificar.
5. Runner self-hosted con capacidad de ejecutar el workflow de deploy.
6. Configuracion mobile modo 644 que debe permanecer limitada a valores publicos.

## Problemas de mantenibilidad

- Dos stacks y dos repos activos con operaciones distintas.
- Servicios y checkouts historicos habilitados/sucios alrededor del runtime real.
- Deploy, restart y escrituras DB acoplados.
- Certificados, timers y nombres heredados sin autoridad clara.
- Los scripts HML de status, health, backup y limpieza son nuevos; requieren
  conservar owner, permisos y seguimiento de su primera ejecucion automatica.
- Diferencias de runtime frente a QA no documentadas antes de este inventario.

## Problemas de migrabilidad

- 48 GiB de media sin backup/checksum probado.
- DB remota sin evidencia de backup/restore.
- Frontend movil debe migrarse junto con backend y NGINX.
- `.env` de ambos repos debe recrearse por canal seguro.
- Runner, TLS, cron, monitoreo y DNS requieren reinstalacion/configuracion.
- Checkouts historicos no deben copiarse automaticamente como parte del runtime.

## Seguro aplicar ahora

1. Mantener este inventario y la comparacion QA/HML.
2. Monitorear Stage 1 de MySQL local y conservar su backup/rollback.
3. Identificar responsable y fuente del certificado sin cambiarlo.
4. Obtener evidencia de backups DB/media.
5. Mantener scripts HML en modo informativo por defecto y documentar cada
   ejecucion aplicada.

## Requiere aprobacion

- crear nuevos backups remotos de configuracion;
- repetir o ampliar la poda de imagenes/build cache Docker;
- modificar o retirar el cron de mantenimiento;
- renovar/reemplazar certificado, editar o recargar NGINX;
- reactivar o purgar MySQL local y borrar su datadir/backup;
- editar comentarios o valores de `.env`;
- cambiar permisos/owners, incluido `/var/www/SISOC` y `.env` mobile;
- detener `sisoc.service`, Apache o el proceso `docker compose logs -f`;
- mover/borrar checkouts historicos, CSV, logs o media;
- restart, deploy, merge de branches o migraciones DB.

## No conviene tocar todavia

1. Media y checkouts historicos hasta tener backup y clasificacion.
2. Purge, paquetes y datadir MySQL antes del 2026-07-20 y sin cierre formal de
   la observacion.
3. Historia de `homologacion` hasta revisar por que diverge de development.
4. Apache/Certbot/sisoc.service hasta entender dependencias y certificado.
5. Permisos amplios de paths heredados mediante cambios masivos.
