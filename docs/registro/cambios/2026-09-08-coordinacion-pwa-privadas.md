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

## Validacion

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
