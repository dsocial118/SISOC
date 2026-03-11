# Tests de regresión para PR 1297 (Celiaquía)

Fecha: 2026-03-10

## Contexto

Durante la revisión del PR 1297 se detectó falta de cobertura de regresión en cambios funcionales sensibles.

## Cambios realizados

- Se agregó `celiaquia/tests/test_expediente_delete.py` con cobertura de:
  - eliminación por superusuario (soft delete),
  - rechazo por permisos para usuario no superuser (`403`),
  - respuesta idempotente para expediente inexistente (`already_deleted=true`).
- Se agregó test unitario `test_consolida_beneficiario_que_tambien_es_responsable` en `tests/test_importacion_service_helpers_unit.py` para validar:
  - actualización de rol a `beneficiario_y_responsable`,
  - generación del warning general de consolidación.

## Impacto

- Mejora cobertura de regresión para flujos modificados por el hotfix.
- No altera contratos funcionales ni comportamiento de producción.
