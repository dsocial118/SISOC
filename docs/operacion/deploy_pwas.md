# Despliegue de PWA privadas

## Alcance y estado

SISOC coordina `main` de las PWA habilitadas al desplegar `homologacion` en HML
o `main` en PRD. Se mantienen el gate de production, sus revisores y la
serializacion actual. QA no incorpora satelites. Un push a una PWA no dispara
por si solo un despliegue.

Esta entrega implementa la coordinacion y genera configuraciones Nginx; no
aprovisiona credenciales, fusiona ramas ni modifica servidores automaticamente.
DataCalle y Gestionar estan habilitadas en el registro de esta entrega; su
activacion depende del empaquetado Compose en main y del orden indicado abajo.
Espacios conserva `/mobile/` y esta entrega habilita ademas
`/pwa/espacioscomunitarios/` sin redirigir la ruta anterior. Requiere primero
la imagen con ambos builds de Espacios; ver el orden de instalacion abajo.

Estado verificado el 2026-09-09: las tres PWA ya estan sirviendo en HML y PRD.
Los bundles activos usan el backend correspondiente a cada entorno. Las notas
de aprovisionamiento del 2026-09-08 siguientes son historicas, no pendientes
actuales. La nueva ruta de Espacios requiere instalar el cambio de esta entrega;
la aceptacion funcional, de instalacion y offline queda al equipo de testers.

| ID | Repositorio privado | Checkout hermano de SISOC | Proyecto / puerto | Estado |
| --- | --- | --- | --- | --- |
| espacios | dsocial118/Espacios-Comunitarios | SISOC-Mobile | sisoc-mobile / 8080 | habilitada, base /mobile/ |
| datacalle | dsocial118/DataCalle | DataCalle | sisoc-pwa-datacalle / 8081 | habilitada, base /pwa/datacalle/ |
| gestionar | dsocial118/Gestionar | Gestionar | sisoc-pwa-gestionar / 8082 | habilitada, base /pwa/gestionar/ |

Fuente de configuracion: `scripts/operacion/pwas.json`. No renombrar las carpetas
historicas ni los proyectos Compose al cambiar un nombre en GitHub.

Estado del aprovisionamiento del 2026-09-08: acceso privado a los tres repos
verificado en HML/PRD, include inicial de Nginx instalado y build de Espacios
preparado en HML sin activacion. DataCalle y Gestionar ya estan clonados en
`/sisoc/DataCalle` y `/sisoc/Gestionar` en ambos hosts, rama main y propietario
sisoc-deploy. El permiso sudo temporal fue retirado y su revocacion verificada.
Los servidores todavia conservan el include inicial de Espacios; este cambio
versionado no equivale a un despliegue. Ver evidencia inicial en
[registro operativo](../registro/cambios/2026-09-08-coordinacion-pwa-privadas.md).

## Orden de primera activacion de DataCalle y Gestionar

1. Incorporar el empaquetado de ambas apps en sus ramas main: Dockerfile y
   Compose en la raiz, servicio frontend y build con API especifica del entorno.
   No promover esta activacion de SISOC a HML/PRD antes: prepare requiere esos
   archivos en main y falla si faltan.
2. Como sisoc-deploy, crear un `.env` modo 600 en `/sisoc/DataCalle` y
   `/sisoc/Gestionar`, sin sobrescribir uno existente. Basta un comentario: las
   variables publicas necesarias las fija SISOC. Los originales privados en
   `~/.config/sisoc-pwa/*/original.env` no se usan en estas PWA; no copiar las
   credenciales AppSheet al frontend.
3. Resolver o validar el backend de HML: el 2026-09-08 el endpoint publico
   `/api/datacalle/relevamientos/` devolvio 404 HTML en HML y 401 JSON en PRD.
   Publicar el frontend no crea esa API. Validar tambien contratos, permisos y
   login de Gestionar; un 401 sin autenticar no prueba funcionalidad.
4. Preparar las imagenes y desplegar primero SISOC homologacion en HML con sus
   gates habituales. Cuando los tres upstreams respondan, respaldar el snippet
   vigente e instalar el candidato con las tres apps. Ejecutar nginx -t y reload.
   Hasta instalar el snippet nuevo, las nuevas rutas no son accesibles.
5. Probar en HTTPS real login, permisos, instalacion y sincronizacion, incluyendo
   desconexion/reconexion. Despues repetir la promocion habitual y la instalacion
   del snippet en PRD, manteniendo su gate de autorizacion.

Los builds locales y los builds/arranques aislados en los hosts HML/PRD estan
verificados. Estos resultados no sustituyen activacion ni flujos autenticados.

Actualizacion operativa del 2026-09-08: el usuario restablecio el permiso temporal
y se verifico acceso como sisoc-deploy en ambos hosts. Se crearon los `.env` de
DataCalle y Gestionar en la raiz de sus checkouts, propietario sisoc-deploy y modo
600, con un comentario y sin secretos. Gestionar incorpora el empaquetado en
main (`df4bce1a267e486326a2d3dd068268d7b618f8f0`) y DataCalle tambien
(`56436c67a319140ccada38c862eba6f65fcf188a`). El usuario recupero espacio en HML;
despues de los builds quedan 20 GB libres (79% de uso). PRD conserva 576 GB.
Las tres imagenes por entorno estan preparadas y pasaron health aislado, usuario
101 y filesystem read-only, sin puertos publicos. Se retiraron los contenedores
de prueba; los servicios en uso no cambiaron. Nginx vigente pasa nginx -t.

Estados privados de esta preparacion (no son una activacion ni reemplazan al
prepare del proximo workflow):

- HML: `~/.local/state/sisoc-pwa-ready-hml-20260908T202244Z/release/state.json`.
- PRD: `~/.local/state/sisoc-pwa-ready-prd-20260908T202540Z/release/state.json`.

Falta incorporar la API de DataCalle de los PRs SISOC #2452/#2453 a development
y luego a homologacion: config/urls.py solo expone api/datacalle en main y el
endpoint publico de HML sigue en 404. El PR #2474 ademas registra tres fallos de
tests de Admisiones en la ejecucion 34272694992, sin cambios en esos formularios
en este diff. Resolver esos gates antes de promover; los 29 tests operativos
acotados pasan. No se modifico Nginx ni se activaron las apps nuevas.
El acceso temporal queda pendiente de retiro al completar la instalacion o
cerrar la intervencion.

### Restablecer acceso temporal para la instalacion

Ejecutar como root en HML y PRD. El bloque permite al operador existente trabajar
como runner y, como root, instalar solamente el snippet PWA, validar/recargar
Nginx y retirar el permiso. No instala las apps ni recarga Nginx al ejecutarlo.

```bash
(
  set -eu
  umask 077
  pwa_sudoers=$(mktemp)
  trap 'rm -f "$pwa_sudoers"' EXIT
  cat > "$pwa_sudoers" <<'SUDOERS'
jportilla ALL=(sisoc-deploy) NOPASSWD: /usr/bin/bash -s
jportilla ALL=(root) NOPASSWD: /usr/bin/install -o root -g root -m 0644 /home/jportilla/sisoc-pwa-nginx.conf /etc/nginx/snippets/sisoc-pwas.conf, /usr/sbin/nginx -t, /usr/bin/systemctl reload nginx, /usr/bin/rm -f /etc/sudoers.d/sisoc-pwa-temporal
SUDOERS
  visudo -cf "$pwa_sudoers"
  install -o root -g root -m 0440 "$pwa_sudoers" /etc/sudoers.d/sisoc-pwa-temporal
)
```

Al terminar la instalacion, retirar `/etc/sudoers.d/sisoc-pwa-temporal` y verificar
que `sudo -n -H -u sisoc-deploy /usr/bin/bash -s` vuelva a ser rechazado para
jportilla. No confundir este acceso administrativo temporal con las deploy keys
permanentes del runner.

## Aprovisionamiento previo a fusionar/desplegar

1. Como administrador del host, habilitar acceso al usuario operativo
   `sisoc-deploy`, con ownership correcto de los checkouts y espacio suficiente
   para snapshots y dos versiones de cada imagen. No corregir errores de Git
   mediante un chown generico al fallar cualquier fetch.
2. Crear una clave ed25519 de solo lectura por app y entorno. La configuracion
   espera `~/.ssh/sisoc-pwa-espacios`, `~/.ssh/sisoc-pwa-datacalle` y
   `~/.ssh/sisoc-pwa-gestionar` del runner. Registrar exclusivamente las claves
   publicas en Settings > Deploy keys del repositorio respectivo, sin escritura.
   Primero solo son necesarias las de Espacios para HML y PRD. Las otras pueden
   provisionarse antes de activar sus apps. No reutilizar una clave entre repos.
3. Verificar las claves de host de github.com con la fuente oficial y preparar
   known_hosts del runner. El coordinador exige StrictHostKeyChecking=yes y no
   solicita passwords. Si ya existe un mecanismo de servicio equivalente, se
   puede definir ssh_identity=null tras validarlo; nunca copiar tokens personales
   a las URLs de Git.
4. Como runner, comprobar lectura del remoto canonico con la identidad elegida.
   Los checkouts habilitados deben existir, tener rama main, no contener cambios
   tracked y ser ancestros de main remoto. No usar la rama en trabajo del usuario.
5. Mantener el `.env` propio de cada entorno en el checkout. No guardarlo en Git.
   La carpeta privada `.deploy/pwa/` se crea dentro del checkout SISOC; queda
   ignorada por Git. No compartirla por HTTP ni recolectarla en artefactos publicos.

Ejemplo de comprobacion (HML, ejecutado COMO sisoc-deploy, despues de registrar la
clave publica; repetir en PRD con su propia clave):

```bash
GIT_SSH_COMMAND='ssh -i ~/.ssh/sisoc-pwa-espacios -o IdentitiesOnly=yes -o BatchMode=yes -o StrictHostKeyChecking=yes' \
  git ls-remote git@github.com:dsocial118/Espacios-Comunitarios.git refs/heads/main
```

Usar el path absoluto a la clave si el shell/SSH no expande `~` en ese contexto.
El coordinador siempre resuelve el path antes de invocar SSH. No leer ni copiar
la clave privada al chat o a los logs.

## Contrato minimo para las apps convertidas

La conversion funcional pertenece al usuario. Antes de habilitar cada app,
acordar o agregar su empaquetado operativo con este contrato (no se exige Vite):

- `compose.yaml` y `compose.prod.yaml` en la raiz del repo, cuyo unico servicio
  resuelto sea `frontend`. Compose construye la imagen y respeta
  `<proyecto>-frontend:${IMAGE_TAG}`. Ejemplo DataCalle:
  `image: sisoc-pwa-datacalle-frontend:${IMAGE_TAG}`.
- Imagen de frontend estatico, no-root, que sirve en 8080, funciona con filesystem
  de solo lectura y tmpfs `/tmp` y `/var/cache/nginx`. Debe incluir `wget` para
  comprobar su raiz HTTP. No contiene base de datos, mounts persistentes ni
  secretos de servidor. El runtime se administra desde SISOC, no desde servicios
  adicionales que pudiera definir la app.
- Build reproducible desde el lockfile y un snapshot limpio del SHA. Los archivos
  Compose mapea `VITE_PUBLIC_BASE_PATH` al nombre que use el framework. Espacios
  conserva `VITE_API_BASE_URL=/api`. Para Expo, `PWA_API_BASE_URL` es
  `https://hml-sisoc.secretarianaf.gob.ar/api` en HML y
  `https://sisoc.secretarianaf.gob.ar/api` en PRD. El coordinador fija estos valores
  despues de leer el ambiente; no pueden heredar por accidente la API de otro
  entorno. DataCalle usa EXPO_PUBLIC_SISOC_API_URL y Gestionar
  EXPO_PUBLIC_API_BASE_URL, con autenticacion api. No usar build:production de
  DataCalle en HML porque fija la URL de PRD.
- DataCalle debe generar recursos/router/manifest/SW bajo `/pwa/datacalle/`;
  Gestionar bajo `/pwa/gestionar/`. No depender de rutas de assets en `/`.
  Limitar el scope del SW a la app y usar nombres propios para caches y
  almacenamiento local; las tres comparten origen y no deben limpiar datos de
  otra PWA durante una actualizacion.
- Los `.env` se usan fuera del contexto Docker para interpolar configuracion;
  revisar que Compose solo pase variables publicables al build. Todo argumento
  incorporado al JavaScript es publico para los usuarios de la app.
- Probar login, permisos, offline/sincronizacion e instalacion. El health de Docker
  solo demuestra respuesta HTTP del frontend, no esos flujos.

Para activar: provisionar checkout/clave/.env, validar build y navegacion en HML,
cambiar `enabled` a true por PR y regenerar el include activo de Nginx. Una app
habilitada que falla bloquea la operacion; no se omite silenciosamente. Hasta ese
momento no requiere checkout ni credenciales y no publica un upstream roto.

## Secuencia y recuperacion

El workflow extrae herramientas y registro desde el SHA de SISOC del evento, no
desde el helper viejo instalado. `SISOC_ROOT_DIR` permite al helper extraido operar
sobre el checkout real sin editarlo a mano ni omitir sus controles.

1. `prepare` valida todos los checkouts habilitados y descarga main desde una URL
   explicita permitida. Fija una vez cada SHA, sin modificar el origin ni hacer
   checkout/merge sobre las carpetas de las PWA. Esas carpetas quedan como caches
   de fuentes; el SHA desplegado se consulta en el estado, no en su HEAD local.
2. Extrae snapshots sin `.git`, archivos ignorados ni el `.env` externo. Rechaza
   enlaces/rutas escapadas. Construye todas las imagenes antes del downtime del
   backend y fija sus IDs Docker, ademas de las etiquetas entorno-SHA.
3. SISOC se despliega con `--without-mobile`; pasan los controles existentes de
   migraciones y salud del backend antes de llamar `activate`.
4. `activate` verifica que ningun contenedor anterior haya cambiado durante la
   preparacion. Reemplaza un frontend por vez y espera su health. Nunca vuelve a
   consultar main, baja todos los stacks juntos ni elimina volumenes.
5. Si falla una app con imagen anterior, intenta reponerla y comprobar salud.
   Un rollback exitoso sigue marcando el deploy como fallido/parcial; las apps ya
   actualizadas no se revierten en silencio. Si no hay version anterior o falla
   la recuperacion, requiere intervencion. No revierte migraciones del backend.

`state.json`, runtime.json y rollback.json quedan en la release privada indicada
en el resumen de Actions. Conservarla para diagnostico y recuperacion junto con
las imagenes previas. No hay limpieza automatica de releases en esta entrega;
monitorear espacio y definir retencion antes de acumular despliegues prolongados.
La salida de subprocess no se publica para evitar filtrar credenciales o valores
de build; un fallo identifica la herramienta y la etapa. Diagnosticar con un
operador en el host sin pegar salidas de `.env`/Compose en logs publicos.

Recuperacion manual de UNA app usando el archivo generado por un fallo:

```bash
docker compose --project-name sisoc-mobile -f /ruta/release/espacios/rollback.json \
  up -d --no-build --pull never --wait --wait-timeout 90 frontend
```

Comprobar primero entorno, proyecto, imagen previa y compatibilidad del frontend
con el backend vigente. No hacer publico el repositorio como mecanismo de rollback.

## Nginx por entorno

En los dos hosts inspeccionados, el vhost esta en
`/etc/nginx/sites-available/sisoc`. HML usa `hml-sisoc.secretarianaf.gob.ar` y PRD
`sisoc.secretarianaf.gob.ar`. No reemplazar los vhosts reales por una plantilla:
conservar TLS, cabeceras, limites y rutas Django/static/media.

Generar un candidato nuevo; el comando rechaza sobrescribir archivos:

```bash
python3 scripts/operacion/render_pwa_nginx.py \
  --config scripts/operacion/pwas.json --output /tmp/sisoc-pwas-candidato.conf
```

Dentro del server HTTPS canonico, sustituir los bloques PWA anteriores por un
unico `include /etc/nginx/snippets/sisoc-pwas.conf;`. Copiar el candidato a esa
ruta solo despues de revisar el diff, respaldar el include/vhost anterior y
comprobar upstreams. Ejecutar `nginx -t` y recargar Nginx. Repetir por entorno,
primero HML y luego PRD. El generador no instala nada ni ejecuta sudo/reloads.

`docs/operacion/nginx/sisoc-pwas.conf` es el candidato activo de esta entrega:
`/mobile/`, `/pwa/espacioscomunitarios/`, `/pwa/datacalle/` y `/pwa/gestionar/`, con aliases `/mobile2/` y
`/mobile3/`. El archivo del repositorio no acredita su instalacion en los hosts.
`sisoc-pwas-preview.conf.example` muestra ademas la ruta final de Espacios;
NO instalar esa vista previa mientras su migracion de clientes este pendiente.

Las redirecciones de navegacion son inicialmente 302 y preservan sufijo/query.
Usan rutas relativas al origen, de modo que HML no redirige hacia PRD. Las rutas
canonicas conservan el proxy loopback. DataCalle/Gestionar eliminan el prefijo
externo; Espacios conserva el nuevo prefijo para seleccionar su segundo build.

Para activar la convivencia de Espacios:

1. Incorporar el Dockerfile dual de Espacios a main y preparar su imagen. Esta
   contiene la app anterior en la raiz y el build nuevo en
   `/usr/share/nginx/html/pwa/espacioscomunitarios/`.
2. Verificar imagen, ambas rutas, manifest y assets antes de reemplazar el
   contenedor. Cada build usa su router y scope; ambos manifiestos conservan ID
   `/mobile/`. El almacenamiento local sigue compartido por origen.
3. Activar la imagen saludable, respaldar el include actual y agregar el proxy
   nuevo hacia `127.0.0.1:8080/pwa/espacioscomunitarios/`. Validar Nginx y recargar.
4. Repetir en PRD luego de HML. Conservar imagen/include anteriores para rollback.

El generador sigue bloqueando reemplazar la base `/mobile/` o redirigirla por
accidente. No se redirige su service worker ni se borran datos de navegadores.
Las pruebas de clientes instalados y sincronizacion las realiza el equipo de
testers. Diseno: `docs/plans/2026-09-09-espacios-rutas-coexistentes-design.md`.

El empaquetado nuevo conserva la imagen anterior para rollback, pero no sirve
assets exclusivos de builds anteriores desde la imagen nueva. Antes de releases
sucesivas, validar una actualizacion con una PWA ya instalada y trabajo pendiente;
no confundir retencion de imagenes con disponibilidad HTTP de assets antiguos.

## Validacion acotada

```bash
# Pruebas puras de operacion: sin Django, Docker real, red ni bases.
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest -q -c pyproject.toml \
  --confcutdir=tests --noconftest -p no:cacheprovider --import-mode=importlib \
  tests/test_deploy_pwas.py tests/test_deploy_refresh_script.py \
  tests/test_deploy_workflow.py tests/test_pwa_nginx.py
bash -n scripts/operacion/deploy_refresh.sh
```

Validar ademas sintaxis del YAML y de cada `run` del workflow, `nginx -t` de los
candidatos y, antes de aplicar, fetch/build como runner y smoke funcional de HML.
Las ultimas comprobaciones contra servidores son distintas de estas pruebas
simuladas. Durante la inspeccion previa, sudo como runner estaba pendiente y el
HTTPS directo a Nginx local rechazo el certificado por vencimiento; verificar la
ruta TLS efectiva antes de reportar validacion publica.
