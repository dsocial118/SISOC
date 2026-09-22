# Deploy independiente de satelites y promocion secuencial

Estado: implementado en rama operativa; activacion de GitHub y servidores
pendiente de validacion final.

## Cambio

- SISOC deja de construir o activar Espacios Comunitarios, DataCalle y
  Gestionar durante su propio deploy.
- Cada repositorio satelite despliega `main` en produccion, `homologacion`
  en HML y `development` en QA.
- La promocion descendente ocurre solamente despues de un deploy verificado:
  `main -> homologacion -> development`.
- SISOC conserva el gate nativo del Environment `production`, con
  `juanikitro`, `Mkdir-arg` y `dsocial118` como revisores.
- En los satelites del plan gratuito, un push a `main` no despliega. Produccion
  se inicia manualmente con `workflow_dispatch` y el workflow solo acepta como
  actor a esos mismos tres usuarios.
- Un run obsoleto no puede promover la punta nueva de una branch.

## Recuperacion

Los satelites restauran la imagen anterior si falla el contenedor o la URL
publica y comprueban el ID restaurado. SISOC restaura el commit anterior,
reconstruye el stack y repite `migrate --check` y el healthcheck.

El rollback de SISOC no revierte migraciones de base de datos. Los cambios de
schema incompatibles requieren la estrategia de migracion/backup especifica de
la release.

## Infraestructura

QA se sirve por HTTP en `10.80.9.15`, solo mediante VPN, sin dominio ni TLS.
Conserva los aliases de produccion: `/mobile/`,
`/pwa/espacioscomunitarios/`, `/pwa/datacalle/`, `/mobile2/`,
`/pwa/gestionar/` y `/mobile3/`.

`scripts/infra/install_qa_pwa_nginx.sh` instala en forma transaccional el
snippet canónico dentro del vhost HTTP existente. Crea backup root-only, exige
un solo `location /`, ejecuta `nginx -t`, recarga y restaura la configuración
anterior ante cualquier fallo.

Los tres runners pasan de estar registrados solo en `secretarianaf/SISOC` a
estar registrados en la organizacion. El grupo organizacional queda limitado a
los cuatro repositorios SISOC. La migracion instala primero un runner paralelo,
lo valida con un job y solo despues retira el servicio anterior, para no dejar
los despliegues sin ejecutor ni mezclar labels entre entornos.

El gate de los satelites vive en el workflow porque GitHub no ofrece Required
reviewers para estos Environments bajo el plan actual. Como se decidio no
proteger sus branches, un usuario con escritura tambien podria modificar ese
control en un cambio posterior; el equipo debe tratar los permisos de escritura
como acceso operativo de confianza.
