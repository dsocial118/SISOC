# Produccion: preparacion y mantenimiento nocturno completo

## Objetivo

Preparar y ejecutar una ventana controlada sobre el productivo canonico
`prd-old` (`10.80.5.45`) durante la noche del 2026-07-14, dejando cada cambio
respaldado, verificable y reversible.

La estrategia aprobada divide el trabajo en dos subventanas:

1. mantenimiento host-side y observacion;
2. promocion del deploy automatico de SISOC-Mobile y deploy productivo.

## Alcance aprobado

- verificar conectividad, health, DB remota, disco, Git, Docker y workers;
- verificar evidencia de backup de DB y el snapshot local de media;
- respaldar configuracion critica en una ubicacion root-only;
- reemplazar la poda Docker agresiva por retencion de 14 dias sin volumenes;
- retirar dos entradas cron que apuntan a paths inexistentes;
- agregar rotacion para los logs NGINX bajo `/sisoc/logs/nginx`;
- restringir `/sisoc/SISOC-Mobile/.env` a `root:sisoc-deploy` modo 640;
- aplicar Stage 1 reversible al MySQL local del app host;
- deshabilitar el arranque futuro de `apache2` y `sisoc.service`, hoy fallidos;
- preparar, revisar, mergear y desplegar el cambio que incorpora
  SISOC-Mobile al deploy de produccion;
- desplegar el release pendiente de `main`, incluido PR #2048 y la migracion
  aditiva `centrodeinfancia.0036_asistenciatrabajador`;
- documentar evidencia, resultado y rollback disponible.

## Exclusiones

- TLS, por decision explicita del responsable;
- purge de MySQL, paquetes o `/var/lib/mysql`;
- borrado de media, logs, imagenes, volumenes, checkouts o backups;
- migraciones manuales o comandos SQL ad hoc que modifiquen datos; la migracion
  automatica `0036_asistenciatrabajador` esta aprobada como parte del release;
- cambios de versiones, dependencias, Docker, NGINX, MySQL o sistema operativo;
- limpieza manual Docker durante la ventana;
- copia externa de media mientras no exista un destino aprobado.

## Baseline confirmado

Preflight read-only del 2026-07-14 10:52 ART:

- host `mdsldmz-ssies`;
- filesystem raiz: 785 GB, 155 GB usados, 598 GB libres, 21%;
- inodos: 2%;
- Docker, containerd, NGINX, cron y runner de produccion activos/habilitados;
- MySQL local activo/habilitado;
- `apache2` y `sisoc.service` fallidos/habilitados;
- siete contenedores activos; SISOC-Mobile healthy;
- `/`, `/health/` y `/mobile/` respondieron 200;
- backend en `main`, commit `980c2b05397b3a18bdcd5853763c6942632232ed`,
  solo `tmp/` no trackeado;
- mobile en `main`, commit `ec7c163fede8b3877fff0fd7863f0a7812043c2c`,
  solo `.env` no trackeado;
- todos los contenedores observados tenian `RestartCount=0`;
- snapshot local de media existente:
  `/sisoc/backups/media/20260713_172352/media`.

Despues de este baseline, `main` avanzo a
`cabcabdaf96ec0ec6723be6695ecc02e460e8615` por el merge de PR #2048. Ese
release todavia no esta desplegado en PRD y forma parte explicita de la ventana.
Existe un workflow productivo anterior en espera de aprobacion, run
`29338795554`, que desplegaria PR #2048 sin mobile. No se debe aprobar: se cancela
en el Gate 5 antes de mergear el PR mobile, evitando dos deploys consecutivos.

Este baseline se debe repetir antes de cada subventana. No se usa como evidencia
si tiene mas de 30 minutos.

## Decisiones de ejecucion

### Secuencia elegida

Se ejecutan cambios pequenos y reversibles primero. El deploy queda ultimo para
no mezclar una falla de configuracion del host con una falla de build/runtime.

El root crontab se transforma una sola vez: se reemplaza la poda Docker y se
retiran las dos lineas legacy en la misma instalacion, con un unico backup
original. Esto evita dos escrituras y rollbacks ambiguos.

### Alternativas descartadas

- Una unica pasada sin checkpoints: dificulta identificar la causa de un fallo.
- Desplegar mobile antes del mantenimiento host-side: mezcla el mayor radio de
  impacto con cambios todavia no validados.
- Ejecutar purges o limpiezas para ganar espacio: el disco esta al 21% y no lo
  justifica.

### Release de aplicacion aprobado

El delta productivo `980c2b053...cabcabdaf` incluye PR #2048:

- funcionalidad de asistencia de trabajadores CDI;
- migracion nueva `0036_asistenciatrabajador`;
- cambios de modelos, views, URLs, templates y CSS;
- tests especificos de asistencia y regresiones CDI;
- checks de `main` completados correctamente antes de la ventana.

La migracion solo crea una tabla, su indice y constraints; no altera tablas
existentes. Django puede revertirla eliminando la tabla, pero ese rollback
borraria cualquier asistencia creada despues del deploy. Por eso el rollback
operativo revierte codigo sin desmigrar automaticamente. Una desmigracion exige
aprobacion de datos separada y confirmacion de que la tabla sigue vacia.

La revision previa del release dejo dos riesgos funcionales abiertos:

- la carga POST de asistencias ejecuta multiples `update_or_create` sin una
  transaccion unica; un error intermedio podria dejar una carga parcial. Ademas,
  una fecha invalida cae en la fecha actual y cualquier marca distinta de `1`
  se interpreta como ausencia;
- `observaciones` existe en modelo y POST, pero la UI la envia oculta y no permite
  verla ni editarla, aunque el registro funcional la describe como editable.

Los checks verdes no cubren fecha invalida, rollback de una carga interrumpida ni
edicion real de observaciones desde la UI. Son riesgos conocidos del release, no
de la migracion. Antes del Gate 5 se requiere una decision explicita entre
corregirlos mediante un PR separado y revalidar, o aceptar el riesgo para esta
ventana. No se mezclan correcciones improvisadas con el deploy nocturno.

## Roles minimos

- Operador: ejecuta comandos en `prd-old` y no avanza sin resultado esperado.
- Validador: controla health, contenedores, DB identity y evidencia de rollback.
- Aprobador GitHub: reviewer y aprobador del Environment `production`.
- Responsable DB: confirma backup vigente y restore probado o su evidencia.

Una misma persona puede cumplir mas de un rol, pero no debe ejecutar dos bloques
en paralelo.

## Ventana recomendada

Horario ART propuesto: 22:00 a 02:00.

| Horario | Bloque |
| --- | --- |
| Antes de 21:30 | PR mobile preparado, checks verdes, sin mergear |
| 21:30-22:00 | Gate 0, evidencia DB y backup de configuracion |
| 22:00-22:25 | Root cron y servicios legacy |
| 22:25-22:50 | Logrotate NGINX y permisos `.env` mobile |
| 22:50-23:15 | Stage 1 del MySQL local |
| 23:15-23:45 | Observacion de subventana A |
| 23:45-00:10 | Rebaseline, merge del PR y espera del gate GitHub |
| 00:10-00:40 | Aprobacion y deploy backend/mobile |
| 00:40-01:20 | Observacion de subventana B |
| 01:20-02:00 | Cierre, evidencia y reserva para rollback |

Si el trabajo empieza en otro horario, conservar duraciones y orden.

## Preparacion diurna

### PR mobile

Crear una branch nueva desde el `origin/main` vigente. No reutilizar directamente
la branch historica `codex/mobile-auto-deploy`.

Aplicar el commit ya revisado `f68aca084f911542e53e9f42435b17bb098b533f`.
El diff esperado es solamente:

- `.github/workflows/deploy.yml`;
- `scripts/operacion/deploy_refresh.sh`;
- cuatro inserciones y tres eliminaciones.

Validaciones minimas:

```bash
git diff --check origin/main...HEAD
bash -n scripts/operacion/deploy_refresh.sh
git diff --name-only origin/main...HEAD
```

El PR debe apuntar a `main`, no ser draft, tener checks verdes y quedar sin
mergear hasta aprobar el Gate 5 nocturno.

El script presente hoy en produccion ya reconoce `--with-mobile` y
`--mobile-dir`; por eso el primer workflow puede invocarlos antes de hacer pull.
El commit agrega ademas la exigencia de branch `main` para SISOC-Mobile.

### Material operativo

Antes de la ventana deben estar disponibles:

- `docs/infra/PROD_CHANGE_PROPOSALS.md`;
- este runbook;
- acceso SSH y sudo interactivo;
- acceso GitHub autenticado;
- reviewer y aprobador del Environment disponibles;
- ubicacion/timestamp del ultimo backup DB y evidencia de restore;
- canal de comunicacion durante la ventana.

## Gate 0 - No-go inicial

No iniciar cambios si ocurre cualquiera de estos casos:

- SSH inestable o identidad distinta de `mdsldmz-ssies`;
- menos de 100 GB libres o mas de 80% de disco;
- alguno de los siete contenedores ausente/restarting/unhealthy;
- `/`, `/health/` o `/mobile/` distinto de 200;
- DB Django distinta de `10.80.5.46`, `ldmzsql-sisoc`, `sisoc_local`;
- cambios Git tracked en backend o mobile;
- branch distinta de `main` en cualquiera de los dos checkouts;
- importacion masiva, mailing u otro worker con tarea no interrumpible;
- deploy GitHub en progreso;
- backup DB no confirmado;
- snapshot local de media sin `status=complete`;
- operador, validador o aprobador GitHub no disponibles.

Los no trackeados `tmp/` backend y `.env` mobile son baseline conocido. Cualquier
otro no trackeado se clasifica antes de avanzar.

## Gate 1 - Backup root-only y evidencia

Crear una carpeta unica:

```text
/var/backups/sisoc/night-maintenance/prod/YYYYMMDD_HHMMSS/
```

Debe quedar `root:root`, directorios 700 y archivos 600. Guardar:

- root crontab original y conteos sanitizados;
- `/etc/nginx` y regla logrotate previa, si existe;
- `/etc/mysql`, `auto.cnf` y metadata de `mysql.service`;
- metadata de `apache2`, `sisoc.service`, NGINX, Docker y runner;
- copia root-only del `.env` mobile solo para rollback de permisos;
- commits backend/mobile;
- nombres e IDs de imagenes Docker y restart counts;
- estado de disco, servicios, listeners y health;
- resultado `docker compose config -q` y lista de servicios.

No guardar en salidas o reportes:

- contenido de `.env`;
- variables de `docker inspect`;
- queries, URLs o payloads de logs;
- claves TLS o privadas;
- credenciales DB.

No continuar si el backup no puede releerse con sudo o si el crontab original no
quedo preservado.

## Subventana A - Mantenimiento host-side

### Gate 2 - Root cron y servicios legacy

Preflight obligatorio:

- exactamente una linea Docker con retencion 24h y `--volumes`;
- exactamente una referencia al path legacy bajo `/home/admin-ssies`;
- exactamente una referencia al path legacy bajo `/opt/ssies`;
- entrada HetrixTools preservada;
- los dos paths legacy siguen inexistentes.

Transformacion unica:

- reemplazar Docker por retencion `until=336h`, sin `--volumes`;
- retirar solo las dos lineas de paths inexistentes;
- preservar todo el resto del crontab;
- deshabilitar `apache2` y `sisoc.service`, sin iniciar ni borrar unidades.

No ejecutar `docker prune` esta noche.

Validar conteos exactos, `crontab -l`, NGINX/Docker activos y los tres health 200.
Ante una diferencia, restaurar el crontab original y el enablement previo.

### Gate 3 - Logrotate y permisos mobile

Instalar la regla NGINX ya definida en
`docs/infra/PROD_CHANGE_PROPOSALS.md`, con:

- rotacion diaria o al superar 100 MB;
- 30 rotaciones;
- compresion diferida;
- archivos nuevos `www-data:root` modo 640;
- `USR1` a NGINX, sin restart completo.

Ejecutar primero dry-run. La aplicacion real debe apuntar solamente a la regla
SISOC, no forzar toda la configuracion global. No borrar logs rotados.

Luego respaldar y cambiar `/sisoc/SISOC-Mobile/.env` de `root:root` 664 a
`root:sisoc-deploy` 640. Validar lectura como `sisoc-deploy` y
`docker compose config --services` sin imprimir variables.

Health obligatorio despues de cada cambio. Si falla logging o lectura del
`.env`, restaurar la configuracion/metadata previa antes de avanzar.

### Gate 4 - Stage 1 del MySQL local

Repetir todos los preflights de `PROD_CHANGE_PROPOSALS.md`:

- Django sigue usando DB remota `10.80.5.46`;
- cero schemas de aplicacion locales;
- cero conexiones inesperadas;
- cero eventos habilitados;
- cero replica channels;
- cero miembros Group Replication.

Solo si todos dan cero:

1. completar backup root-only de `/etc/mysql`, `auto.cnf`, unidad y metadata;
2. detener y deshabilitar `mysql.service` local;
3. verificar que desaparecieron listeners 3306/33060 locales;
4. confirmar nuevamente identidad DB remota desde Django;
5. validar siete contenedores y health.

Conservar datadir de 200 MB y paquetes por al menos 14 dias. No ejecutar purge.

Rollback inmediato:

```bash
sudo systemctl enable --now mysql
```

Luego validar servicio, listeners y health. Cualquier consumidor local inesperado
obliga a rollback y cierre del Gate 4.

## Observacion entre subventanas

Duracion minima: 30 minutos.

Cada cinco minutos registrar sin contenido sensible:

- HTTP de `/`, `/health/` y `/mobile/`;
- estado y restart count de siete contenedores;
- identidad DB remota;
- NGINX activo y logs con crecimiento;
- MySQL local inactive/disabled y sin listener;
- disco e inodos;
- journal por conteos de errores, sin copiar mensajes con PII.

No abrir la subventana B ante un solo health fallido, restart count nuevo, error
NGINX, DB identity distinta o rollback pendiente.

## Subventana B - Deploy backend y SISOC-Mobile

### Gate 5 - Merge y aprobacion

Antes del merge:

- PR mobile con diff exacto y checks verdes;
- aprobacion de reviewer;
- `main` contiene el release aprobado de PR #2048 y ningun commit adicional no
  clasificado;
- CI no reporta migraciones pendientes;
- no hay trabajos masivos o mailings en curso;
- recapturar commits, imagenes y restart counts;
- repetir health y DB identity;
- confirmar que el rollback de imagenes puede ejecutarse.
- registrar la decision sobre los dos riesgos funcionales abiertos de PR #2048:
  PR correctivo validado o aceptacion explicita del riesgo para esta ventana.

Cancelar el workflow stale `29338795554` y verificar estado `cancelled` antes
del merge. Como `cancel-in-progress` esta deshabilitado para deploys, dejarlo en
espera bloquearia o podria ejecutar un deploy backend-only fuera de secuencia.

Mergear el PR a `main`. El job `deploy-produccion` debe quedar bajo el Environment
`production`. No aprobar el Environment hasta repetir el baseline una ultima vez.

El deploy esperado:

1. baja el stack backend sin volumenes;
2. hace pull `--ff-only` de `main`;
3. reconstruye y levanta Django y cinco workers;
4. baja el stack mobile sin volumenes;
5. hace pull `--ff-only` de mobile `main`;
6. reconstruye y levanta SISOC-Mobile.

Hay indisponibilidad esperada mientras los stacks estan abajo. El entrypoint
backend puede ejecutar migraciones; por eso el backup DB y los checks de
migraciones son gates obligatorios.

### Gate 6 - Verificacion post-deploy

Validar:

- workflow productivo verde;
- backend en el commit mergeado y mobile en el commit esperado;
- working trees sin cambios tracked;
- siete contenedores activos y mobile healthy;
- restart counts estables;
- `/`, `/health/` y `/mobile/` en 200;
- DB remota correcta;
- `showmigrations centrodeinfancia` marca `0036_asistenciatrabajador` aplicada;
- tabla nueva accesible mediante una consulta ORM read-only;
- pagina CDI y acceso a asistencia verificados por un usuario autorizado, sin
  crear datos ficticios;
- static y un media existente accesibles;
- NGINX escribiendo logs;
- workers presentes sin reprocesamientos inesperados;
- runner, cron y monitoreo activos;
- MySQL local sigue inactive/disabled.

Observar durante al menos 40 minutos antes de cerrar.

## Rollback por bloque

| Bloque | Rollback |
| --- | --- |
| Root cron | Restaurar el crontab original root-only y verificar conteos |
| Servicios legacy | Restaurar enablement previo; no iniciar servicios fallidos |
| Logrotate | Restaurar regla anterior o mover la nueva al backup; conservar logs rotados; enviar `USR1` |
| `.env` mobile | Restaurar `root:root` modo 664 desde metadata/copia root-only |
| MySQL Stage 1 | `systemctl enable --now mysql`, validar listeners y health |
| Deploy backend/mobile | Recuperar servicio primero con commits/imagenes registrados; luego revertir el PR mediante otro PR |

El rollback del release de aplicacion no revierte la migracion `0036` durante la
ventana. La tabla puede quedar aplicada y sin uso mientras se revierte el codigo;
esto preserva cualquier registro creado y evita perdida de datos.

Para rollback de runtime Docker, recapturar antes del deploy el nombre e ID de
cada imagen. Si un build falla despues de `compose down`, priorizar levantar los
tags/IDs anteriores con `docker compose up -d --no-build`. No podar imagenes
durante la ventana.

No usar `git reset --hard`, force-push, `docker system prune`, `down --volumes` ni
restauraciones parciales sobre la DB productiva.

Si el checkout debe volver temporalmente a un commit anterior para restaurar
servicio, requiere un GO de emergencia explicito y luego debe normalizarse con
un revert PR; no dejar produccion detached como cierre.

## Criterios de abortar

Abortar el bloque actual, ejecutar su rollback y no avanzar si:

- un conteo preflight no coincide exactamente;
- un backup no puede validarse;
- health deja de responder 200;
- aparece un restart inesperado;
- cambia la identidad DB;
- NGINX deja de escribir;
- un worker reprocesa o pierde una tarea;
- el PR contiene archivos extra, checks fallidos o commits inesperados;
- el deploy excede 20 minutos con un stack abajo;
- falta el operador, validador o aprobador requerido.

Un bloque abortado no autoriza a improvisar una alternativa durante la misma
ventana.

## Evidencia de cierre

Guardar root-only y luego resumir sin secretos:

- timestamp de inicio/fin por gate;
- backup path;
- cambios aplicados y rollback path;
- commits antes/despues;
- imagenes antes/despues;
- estado de servicios, puertos, contenedores, disco e inodos;
- health y DB identity;
- URL del PR y workflow;
- cambios omitidos y causa;
- periodo de observacion y riesgos abiertos.

Actualizar al dia siguiente `PROD_INVENTORY.md`, `PROD_RISKS.md`,
`PROD_CHANGE_PROPOSALS.md` y `PROD_MIGRATION_CHECKLIST.md` mediante PR a
`development`.

## Seguimiento

- observar 24 horas sin borrar backups ni datadir MySQL;
- revisar primera ejecucion del nuevo cron Docker;
- verificar rotacion y permisos de logs NGINX;
- confirmar proximo deploy backend/mobile coordinado;
- definir destino externo para media y prueba de restore;
- mantener TLS fuera hasta una autorizacion separada.

## Datos pendientes antes de ejecutar

1. hora final de inicio si difiere de 22:00 ART;
2. responsable y evidencia del backup DB/restauracion;
3. confirmacion de que no habra importaciones/mailings durante la ventana;
4. reviewer y aprobador GitHub disponibles;
5. destino externo de media, si se quiere incluir esa copia en otro trabajo.

La aprobacion de este diseño permite preparar scripts/PRs y la ventana. La
ejecucion productiva comienza solamente con un GO explicito al Gate 0.
