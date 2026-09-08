# Despliegue de PWA privadas

## Alcance y estado

SISOC coordina `main` de las PWA habilitadas al desplegar `homologacion` en HML
o `main` en PRD. Se mantienen el gate de production, sus revisores y la
serializacion actual. QA no incorpora satelites. Un push a una PWA no dispara
por si solo un despliegue.

Esta entrega implementa la coordinacion y genera configuraciones Nginx; no
aprovisiona credenciales, fusiona ramas ni modifica servidores automaticamente.
DataCalle y Gestionar estan deshabilitadas: el usuario convierte esas apps por
separado. Espacios conserva `/mobile/` hasta validar la migracion de sus clientes.

| ID | Repositorio privado | Checkout hermano de SISOC | Proyecto / puerto | Estado |
| --- | --- | --- | --- | --- |
| espacios | dsocial118/Espacios-Comunitarios | SISOC-Mobile | sisoc-mobile / 8080 | habilitada, base /mobile/ |
| datacalle | dsocial118/DataCalle | DataCalle | sisoc-pwa-datacalle / 8081 | deshabilitada |
| gestionar | dsocial118/Gestionar | Gestionar | sisoc-pwa-gestionar / 8082 | deshabilitada |

Fuente de configuracion: `scripts/operacion/pwas.json`. No renombrar las carpetas
historicas ni los proyectos Compose al cambiar un nombre en GitHub.

Estado del aprovisionamiento del 2026-09-08: acceso privado a los tres repos
verificado en HML/PRD, include inicial de Nginx instalado y build de Espacios
preparado en HML sin activacion. DataCalle y Gestionar ya estan clonados en
`/sisoc/DataCalle` y `/sisoc/Gestionar` en ambos hosts, rama main y propietario
sisoc-deploy. El permiso sudo temporal fue retirado y su revocacion verificada.
Las apps nuevas siguen deshabilitadas. Ver evidencia y pendientes en
[registro operativo](../registro/cambios/2026-09-08-coordinacion-pwa-privadas.md).

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
  Compose pueden mapear `VITE_PUBLIC_BASE_PATH` y `VITE_API_BASE_URL` a los nombres
  que use el framework; esos nombres son el contrato operativo, no una obligacion
  de usar Vite. `/api` usa el mismo origen del entorno; no fijar PRD dentro del JS.
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

`docs/operacion/nginx/sisoc-pwas.conf` es la configuracion inicial activa:
solo `/mobile/`. `sisoc-pwas-preview.conf.example` muestra las tres rutas finales
y sus aliases; NO instalar esa vista previa mientras las apps no esten listas.

Las redirecciones de navegacion son inicialmente 302 y preservan sufijo/query.
Usan rutas relativas al origen, de modo que HML no redirige hacia PRD. Las rutas
canonicas conservan el proxy loopback y eliminan solo el prefijo externo.

La migracion de Espacios a `/pwa/espacioscomunitarios/` requiere otra entrega
coordinada con su cliente: identidad instalada, router, manifest, service worker
anterior y assets. El generador bloquea esa activacion prematura. No redirigir
el script del SW antiguo ni borrar datos pendientes para forzar una actualizacion.
Se debe probar el cambio con una instalacion vieja y acordar su transicion antes
de retirar este bloqueo. No depende de la conversion de DataCalle/Gestionar.

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
