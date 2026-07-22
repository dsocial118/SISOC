# QA - Riesgos iniciales de infraestructura

Estado: actualizado despues del mantenimiento aprobado y del retiro Stage 2 del
MySQL local, corte 2026-07-21.

La clasificacion prioriza continuidad, seguridad y migrabilidad. Se aplicaron
la limpieza Docker, la eliminacion aprobada de dos dumps y el retiro Stage 2
del MySQL local, todos documentados y sin reiniciar la aplicacion.

## Riesgos criticos

### 1. Documentacion historica con identidad QA dividida

El usuario confirmo que `qa-old` en `10.80.9.15` es canonico. Parte de la
documentacion todavia presenta SITE-QA/DB-QA AWS como vigentes, aunque por ahora
son solo referencias de migracion.

Impacto: se puede documentar, migrar, respaldar o apagar el servidor equivocado.

Accion segura: reconciliar la documentacion sin tocar destinos ni GitHub
Environment.

### 2. Filesystem raiz recuperado a 34%

La limpieza Docker, la eliminacion aprobada de dos dumps antiguos y Stage 2
dejaron 62 GB libres. Docker ya no es el componente principal conocido; el
datadir MySQL local de 43 GB ya no existe.

Impacto residual: el espacio ya no bloquea el deploy, pero logs, media y Docker
pueden volver a crecer si no se mantiene el monitoreo.

Accion segura: mantener el cron conservador y monitorear semanalmente capacidad
y journal del mantenimiento.

### 3. Retiro Stage 2 del MySQL local irreversible

Stage 2 purgo los paquetes server y elimino el datadir local de 43 GB. No queda
unidad, binario ni listener local. La aplicacion continuo en la DB canonica
`10.80.9.18`; no se uso `autoremove`.

Impacto aceptado: ya no existe rollback del clon historico local. El backup de
Stage 1 conserva metadatos operativos, no los datos eliminados.

Accion segura: no reinstalar MySQL local ni usar ese backup como fuente de
restauracion. Cualquier nueva instancia local requiere una decision de
arquitectura y plan de datos separado.

El responsable confirmo que este MySQL local no forma parte de la arquitectura:
QA usa `10.80.9.18`. La instancia heredada debe retirarse por etapas, no asumirse
vacia ni borrarse directamente.

### 4. Reiniciar o desplegar escribe en la base automaticamente

El entrypoint web ejecuta ajuste de historial, migraciones, carga de fixtures,
creacion de usuarios de prueba y grupos en cada arranque. El deploy automatico
reinicia el stack, por lo que no existe un restart puramente operativo.

Impacto: una accion presentada como restart/deploy puede modificar schema y datos,
y no cumple una politica de "no migraciones sin aprobacion".

Accion segura: documentar este acoplamiento y no ejecutar restart/deploy hasta
tener backup, rollback y autorizacion explicita para los side effects.

### 5. No hay evidencia de backup vigente ni restore probado

Los dos dumps SQL de 2025 no eran backups validados y fueron eliminados con
aprobacion. No se confirmaron backup actual, retencion, cifrado, copia fuera del
host o prueba de restore para la DB canonica `10.80.9.18`.

Impacto: migracion o incidente sin punto de recuperacion confiable.

Accion segura: identificar la DB realmente usada y obtener evidencia de backups de
Infra antes de cualquier cambio.

### 6. Dumps SQL antiguos eliminados (resuelto)

Los dos paths inventariados fueron eliminados por `admin-ssies` tras aprobacion
explicita. Se verifico su ausencia y QA continuo saludable. No se borraron otros
archivos SQL.

## Riesgos medios

### Deploy con downtime y rollback manual

`deploy_refresh.sh` ejecuta `down` antes de `git pull` y del build. Si pull o build
fallan, el stack queda abajo. El workflow registra el commit previo, pero no hace
backup, health check ni rollback automatico.

### Puerto de aplicacion expuesto directamente

El puerto 8001 escucha en todas las interfaces, ademas del acceso por NGINX. Esto
puede permitir bypass de limites, logging o headers del proxy.

### Puertos 10000/10050 sin owner confirmado

Escuchan en todas las interfaces. Pueden ser legitimos, pero no se pudo asociar
proceso/configuracion con los permisos actuales.

### Apache habilitado pero fallido

Convive con NGINX instalado y habilitado. Agrega ruido operativo, alertas y riesgo
de colision futura de puertos. No deshabilitar hasta conocer por que existe.

### Acceso privilegiado incompleto para cerrar el inventario

Se obtuvo acceso puntual suficiente para inventariar y retirar el MySQL local
en Stages 1 y 2. Todavia falta verificar firewall/ACL, crontab root y la
configuracion efectiva completa de NGINX y servicios.

### Bind mount del repo completo y contenedores como root

La aplicacion monta el checkout entero en `/sisoc/`. Logs recientes quedan
mezclados entre `root` y `sisoc-deploy`, y el entrypoint borra/regenera
`static_root`. Esto complica ownership, backups y una futura migracion.

### Working tree remoto no limpio

Existe un archivo no trackeado con cuatro caracteres ESC. Hoy no bloquea porque el
script solo impide cambios tracked, pero ensucia el estado y podria ocultar un
artefacto inesperado. No inspeccionar ni borrar sin aprobacion.

### Contrato cron historico peligroso y desactualizado

`scripts/crontab` usa paths inexistentes y `docker system prune --volumes`.
`sisoc-deploy` ahora tiene una sola tarea segura y verificada; cron de root sigue
pendiente.

### Certbot duplicado o ambiguo

Hay comando Certbot 5.6.0, paquete apt 1.21 y timer snap, sin certificados live.
Puede ser remanente; no remover hasta entender el mecanismo esperado.

### Documentacion operativa desactualizada

`docs/operacion/infraestructura.md` describe deploy manual y QA AWS, mientras la
realidad observada es CD self-hosted en QA viejo.

## Riesgos bajos

- El virtual host se llama `staging.conf` aunque sirve QA.
- NGINX actua como `default_server` sin `server_name` detectado.
- El checkout de deploy contiene artefactos de desarrollo/documentacion y hojas
  XLSX que no son necesarios para runtime.
- Los logs de aplicacion son numerosos por fecha/nivel, aunque su tamanio total es
  bajo.
- No hay TLS en QA viejo; puede ser aceptable en red interna, pero debe quedar como
  decision explicita.

## Problemas de seguridad

1. Puerto 8001 permite acceso directo a Gunicorn fuera del proxy.
2. Puertos 10000/10050 sin owner o necesidad confirmados.
3. Archivos `.env.*` de entorno estan trackeados; no se revisaron valores y debe
   confirmarse que solo contienen placeholders/no secretos.
4. El runner self-hosted ejecuta codigo de deploy dentro del servidor. Debe seguir
   restringido a workflow/branches confiables y no usarse para PRs.
5. `create_test_users` se ejecuta en arranque; requiere revisar por separado que
   las credenciales y alcance sean adecuados para QA.

## Problemas de mantenibilidad

- Documentacion de dos topologias QA aunque `qa-old` ya fue confirmado canonico.
- Deploy, migraciones, fixtures, usuarios, estaticos y restart acoplados.
- Nombres historicos (`qa-old`, `staging.conf`, path `sisoc-comedores-test`).
- Diagnostico dependiente de un usuario con visibilidad insuficiente.
- Servicios duplicados/remanentes: Apache y multiples Certbot.
- Logs y archivos generados con ownership mixto.
- Documentacion que no refleja el CD real.

## Problemas de migrabilidad

- La app apunta al host canonico `10.80.9.18`, pero falta inventariar su backup.
- No hay backup/restore vigente demostrado.
- Media vive en filesystem local, sin object storage.
- El repo completo se usa como volumen de runtime.
- Docker y MySQL local ya fueron inventariados; falta auditar backup, capacidad
  y restore de la DB remota.
- Runner y cron de `sisoc-deploy` estan inventariados; faltan root y ACL/firewall.
- AWS queda deliberadamente fuera de alcance hasta iniciar una migracion.

## Seguro aplicar ahora

1. Mantener inventario, operaciones y rollback actualizados.
2. Monitorear semanalmente disco y journal del mantenimiento.
3. Mantener ausente el MySQL local; no introducir una dependencia nueva del
   host de aplicacion.
4. Pedir evidencia de backup/retencion/restore de `10.80.9.18`.
5. Comparar GitHub Environment `qa` y label del runner sin cambiar valores.

## Requiere aprobacion

- crear backups nuevos o copiar configuracion sensible;
- cambiar bind de MySQL, firewall, puertos o ACL;
- cambiar permisos/owners de logs, repo o `.env`;
- deshabilitar Apache, Certbot u otro servicio;
- reinstalar MySQL local o intentar reconstruir sus datos historicos;
- ampliar la limpieza a logs, datos, cache reciente o el archivo no trackeado;
- modificar NGINX, Compose, entrypoint, runner, cron o deploy;
- reiniciar/redeployar, porque dispara escrituras en DB;
- migrar o restaurar base de datos;
- mover media o checkout.

## No conviene tocar todavia

1. El QA canonico hasta planificar y validar formalmente una migracion.
2. El archivo no trackeado hasta identificarlo en una sesion controlada.
3. Crontab root y monitoreo historico hasta saber que jobs/agentes existen.
4. Apache/Certbot hasta descartar dependencias ocultas.
5. El orden del deploy sin antes definir rollback, backup y ventana de prueba.
