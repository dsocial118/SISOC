# 2026-08-29 — Dispositivos: preflight declarativo C3.3

## Resultado

Se versiona un contrato público de destinos para QA, homologación y producción
de Dispositivos, junto con un validador Node y un check requerido. El contrato
exige checkout, proyecto Compose, roles y referencias de entorno/rollback
propios del servicio; prohíbe reutilizar `APP_ROOT` del monolito.

## Límites

El check corre en GitHub-hosted y sólo valida archivos versionados. No usa
runners self-hosted, Environments, Docker, secretos, datos reales ni servicios
de QA/HML/PRD. Por eso confirma coherencia del contrato, no provisionamiento
real de la infraestructura.

## Continuidad

El deploy actual de SISOC sigue fuera del flujo: `deploy_refresh.sh` opera el
stack monolítico completo y no es apto para Dispositivos. C3.4 deberá añadir un
preflight manual de sólo lectura sobre cada runner y, luego de autorización por
ambiente, el primer deploy/restart/rollback aislado.
