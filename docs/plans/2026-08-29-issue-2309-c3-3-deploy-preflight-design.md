# #2309 — C3.3: preflight declarativo de despliegue independiente

## Decisión aprobada

Antes de introducir un deploy de Dispositivos, el repositorio validará en CI el
contrato operativo mínimo de cada entorno. El corte no ejecuta Docker, no usa
runners self-hosted, no lee secretos, no modifica checkouts ni interactúa con
QA, homologación o producción.

El objetivo es impedir que C3.4 se implemente sobre el deploy monolítico
existente. Ese deploy invoca `deploy_refresh.sh`, baja y reconstruye el stack
completo; por lo tanto no es reutilizable para Dispositivos.

## Contrato versionado

Un archivo público y sin secretos declara los tres destinos:

| Campo | Propósito |
| --- | --- |
| `branch` | SHA fuente permitido por ambiente (`development`, `homologacion`, `main`). |
| `environment` | GitHub Environment existente (`qa`, `homologacion`, `production`). |
| `runner_labels` | Runner dedicado que C3.4 deberá usar. |
| `app_root_variable` | Variable del Environment que apunta a un checkout exclusivo de Dispositivos, distinto de `APP_ROOT`. |
| `compose_file` y `compose_project` | Composición y nombre de proyecto Docker exclusivos; no pueden usar el stack monolítico. |
| `web_service`, `migrate_service` | Roles que C3.4 podrá iniciar por separado. |
| `env_file_variable` | Referencia a la variable que identifica el archivo de entorno privado, sin exponer su contenido. |
| `rollback_state_variable` | Referencia al estado externo donde C3.4 registrará el SHA previo; el preflight no lo crea ni lo modifica. |

Los nombres de variables son contrato de infraestructura, no valores: su
configuración real permanece en los GitHub Environments o en los runners.

## Implementación

1. Agregar una configuración JSON de destinos bajo `.github/`.
2. Agregar un validador Node puro y tests de matriz: ambientes, branches,
   runners, variables, rutas, project names y roles deben ser completos,
   únicos y compatibles con el runtime actual.
3. Agregar un workflow global de PR que ejecuta sólo esos tests y publica el
   check `dispositivos_deploy_preflight`.
4. Hacer que `deploy_guard` espere ese check. El clasificador C3.2 también
   considerará relevantes la configuración, el workflow y el validador para no
   dejar un cambio operativo fuera del build trazable.

## Criterios de aceptación

- Un PR que altere un destino inválido falla sin ejecutar Docker ni usar un
  Environment.
- Los tres entornos preservan su branch, Environment y labels actuales, pero
  exigen un `DISPOSITIVOS_APP_ROOT` independiente del `APP_ROOT` monolítico.
- Cada destino define proyecto Compose exclusivo, servicios `dispositivos-web`
  y `dispositivos-migrate`, y referencias separadas para entorno privado y
  estado de rollback.
- `deploy_guard` no puede pasar sin el preflight.
- No se publica imagen, no se despliega, no se reinicia ningún servicio y no se
  accede a datos reales.

## Riesgos y reversa

Este corte verifica coherencia declarativa, no prueba que los runners, rutas,
variables o permisos estén provisionados. C3.4 deberá ejecutar un preflight
manual, sólo de lectura, en cada runner antes de habilitar el primer deploy.

Un falso sentido de disponibilidad se evita porque el summary y la
documentación nombran explícitamente esa limitación. Revertir C3.3 elimina el
check y los archivos de contrato; no hay datos, imágenes ni infraestructura que
revertir.

## Fuera de alcance

- Despachar jobs a runners self-hosted o acceder a GitHub Environments.
- Crear checkouts, archivos `.env`, credenciales, estado de rollback, puertos o
  proyectos Docker en un servidor.
- Deploy, migración, restart, routing, health o rollback real. Esos efectos
  empiezan recién en C3.4, con autorización específica por ambiente.
