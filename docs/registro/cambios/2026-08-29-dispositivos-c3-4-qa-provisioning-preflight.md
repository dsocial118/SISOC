# 2026-08-29 — Dispositivos: provisioning QA y preflight C3.4

## Hechos confirmados

- El host QA canónico (`qa-old`) tiene Docker Compose y el runner
  `sisoc-qa` activo bajo el usuario `sisoc-deploy`.
- Se creó un checkout hermano y limpio de `origin/development` para
  Dispositivos, con `.env` privado (`0600`) y estado de rollback privado
  (`0600`) fuera del árbol Git.
- El Environment `qa` ya referencia esos tres recursos mediante
  `DISPOSITIVOS_APP_ROOT`, `DISPOSITIVOS_ENV_FILE` y
  `DISPOSITIVOS_ROLLBACK_STATE`. No se registran valores de paths ni secretos.
- No se ejecutaron Docker, Compose, migraciones, deploys, cambios de datos ni
  reinicios. El proyecto Compose de Dispositivos no tiene contenedores.

## Preflight bloqueado correctamente

El checkout aislado sigue `development`, como exige el contrato de destino. En
esa rama todavía no existe `compose.dispositivos.yml`: el runtime, el Compose y
los gates de #2309 están en el PR draft #2365 y no pueden ejecutarse en un
runner self-hosted antes de integrarse en una rama confiable.

No se cambió el checkout a la rama del PR ni se ejecutó código de una rama draft
en QA. Completar el preflight requiere integrar #2365 en `development` mediante
el proceso de revisión/autorización correspondiente y recién entonces actualizar
el checkout aislado al SHA integrado.

## Reversa

Mientras no exista un deploy, retirar el provisioning implica borrar únicamente
el checkout aislado, su estado de rollback y las tres variables del Environment.
No hay datos, imágenes ni servicios que reconciliar.
