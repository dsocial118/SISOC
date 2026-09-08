# Coordinacion de PWA privadas desde SISOC

## Cambio

Se implementa preparacion de snapshots e imagenes de main de las PWA antes del
downtime de SISOC y activacion posterior a la salud del backend. El workflow usa
las herramientas del SHA aprobado, conserva el gate de production y no amplia QA.
La descarga ya no depende de que Espacios Comunitarios sea publico.

## Decision y alcance

El usuario pidio implementar infraestructura mientras convierte DataCalle y
Gestionar. Ambas permanecen desactivadas en un registro explicito hasta disponer
de builds web verificadas. Espacios conserva `/mobile/` durante esta entrega.
Los tres nombres oficiales son `dsocial118/Espacios-Comunitarios`,
`dsocial118/DataCalle` y `dsocial118/Gestionar`, todos privados.

## Impacto y riesgos

- Requiere identidades Git de solo lectura y checkouts provisionados como runner.
- Runtime limitado a un frontend estatico por app, loopback, sin mounts de datos.
- Estado/imagenes anteriores permiten recuperar una PWA; un fallo parcial nunca
  se informa como exito ni revierte automaticamente datos del backend.
- Las releases privadas se conservan para recuperacion; requieren controlar
  espacio. No se agrego limpieza automatica de imagenes o archivos.
- Nginx tiene generador y candidatos; no modifica servidores. La migracion del
  SW de Espacios debe validarse antes de activar su ruta canonica.

## Validacion inicial, previa al aprovisionamiento

- 28 pruebas pasaron: orquestacion con comandos simulados, helper Bash,
  orden/gates del workflow y generador de Nginx.
- Black 24.8.0: seis archivos Python conformes. YAML del workflow parseado y
  `bash -n` correcto para el helper y sus cuatro bloques run. `git diff --check`
  sin errores.
- Nginx 1.18 en contenedor local aislado, sin puertos publicados: `nginx -t`
  correcto con los dos includes; cinco peticiones verificaron proxy, aliases y
  conservacion de sufijos/query contra upstreams simulados. No prueba los
  certificados ni el vhost completo instalado en los hosts.
- Compose valido para el snapshot de Espacios
  `9e65e5e4ca7967bfbb8240722dea2dfad5b99e40`, variables de base/API e imagen
  versionada correctas. Configuracion runtime tambien validada con Compose.
- No se ejecuto build real de apps, deploy, merge, recarga remota de Nginx ni
  prueba funcional/autenticada de las PWA. SSH directo como sisoc-deploy fue
  rechazado en HML y PRD; sudo no interactivo requiere autenticacion. Quedan
  pendientes el acceso administrativo, las identidades Git y la validacion
  operativa en HML antes de produccion.

Ver [operacion y contrato de build](../../operacion/deploy_pwas.md).

## Aprovisionamiento ejecutado en HML y PRD

- El administrador habilito permisos temporales para operar como sisoc-deploy e
  instalar/validar/recargar los dos archivos previstos de Nginx.
- Se reutilizo la deploy key existente de Espacios en HML y se registraron cinco
  claves nuevas: Espacios PRD, DataCalle HML/PRD y Gestionar HML/PRD. Todas son de
  solo lectura; las claves privadas permanecen en sus servidores.
- Se verifico `ls-remote main` para las seis combinaciones app/entorno. Espacios
  resolvio `f4f61ee61ce2ce7fe9e21475234ecf943c8227a0`; DataCalle y Gestionar
  mantienen los SHA de sus copias iniciales.
- El checkout operativo de Espacios tiene `core.sshCommand` con identidad
  dedicada y una regla local `url.*.insteadOf` para convertir el HTTPS historico
  de SISOC-Mobile a SSH. Esto conserva compatibilidad con el helper instalado,
  que todavia fuerza la URL antigua. El repositorio sigue privado. Se probaron
  fetch real, posibilidad de fast-forward y dry-run del helper en ambos hosts.
- Se instalaron `/etc/nginx/snippets/sisoc-pwas.conf` y la referencia al include
  en el vhost existente, conservando los otros bloques. `nginx -t`, reload y
  servicio activo correctos en ambos hosts; upstream 8080 respondio HTTP 200.
  No se publicaron DataCalle/Gestionar ni las rutas canonicas pendientes.
  Las peticiones a las URLs publicas desde los hosts agotaron el limite de 15
  segundos; no se afirma validacion de navegacion publica ni de TLS externo.
- El coordinador construyo Espacios en HML con el SHA indicado y dejo estado
  `prepared` en `~/.local/state/sisoc-pwa-build-hml-20260908`. No se ejecuto activate,
  no se reiniciaron contenedores ni se desplego SISOC.
- Los `.env` originales proporcionados se guardaron como
  `~/.config/sisoc-pwa/{datacalle,gestionar}/original.env`, modo 600, en ambos
  hosts. Son referencias privadas, no configuraciones de build activas. La
  credencial APPSHEET_API_KEY de DataCalle debe permanecer fuera del frontend.
- Respaldos del Git config de Mobile y del vhost en
  `~/.local/state/sisoc-pwa-provision-20260908/` del runner.
- La clave de host Ed25519 de GitHub se incorporo desde su
  [documentacion oficial](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/githubs-ssh-key-fingerprints),
  conservando StrictHostKeyChecking=yes.

## Cierre del aprovisionamiento

Tras la creacion de directorios por root, se clonaron en HML y PRD:

- `/sisoc/DataCalle`: main en `27140ae5bb5b4a3b119847c4924d387c6b9949ec`.
- `/sisoc/Gestionar`: main en `d249a7105f0a73ca33c00ff6a599d8f03ccdb00c`.

Los cuatro checkouts quedaron limpios, con owner sisoc-deploy:sisoc-deploy,
modo 0750 y `core.sshCommand` apuntando a su clave dedicada. Se comprobo igualdad
entre HEAD y main remoto mediante acceso autenticado, y modo 600 de los `.env`
originales resguardados fuera de los checkouts.

`nginx -t` volvio a pasar en ambos hosts. Se elimino
`/etc/sudoers.d/sisoc-pwa-temporal` y se verifico que jportilla ya no puede ejecutar
el comando autorizado como sisoc-deploy sin autenticacion. Las claves de lectura
del runner permanecen instaladas; su uso por Actions no depende de este sudo.

El PR sigue sin fusionarse. DataCalle/Gestionar permanecen deshabilitadas hasta
completar sus builds web y configuraciones de entorno. La activacion del nuevo
workflow, la migracion de la ruta de Espacios y las pruebas funcionales siguen
siendo pasos separados.
