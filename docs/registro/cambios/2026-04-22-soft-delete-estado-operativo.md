# Soft-delete y estado operativo

Fecha: 2026-04-22

## Que se resolvio

- Se corrigio la desincronizacion entre `deleted_at` y el estado operativo en entidades con soft-delete.
- Antes, el soft-delete marcaba la baja logica pero no siempre dejaba consistente `activo` o `estado`.

## Cambio aplicado

- `core.soft_delete` paso de inferencia implicita a configuracion explicita por modelo para `activo` y `estado`.
- `restore()` ahora reaplica un estado operativo configurable por modelo, en lugar de dejar la entidad restaurada inactiva o cerrada.
- Se agregaron mappings explicitos en VAT para `Centro`, `PlanVersionCurricular`, `TituloReferencia`, `Curso`, `ComisionCurso`, `OfertaInstitucional` y `Comision`.
- Se configuraron tambien `Ciudadano` y `centrodefamilia.Centro` para que el restore reactive `activo=True`.
- Las cascadas quedan cubiertas por la misma logica de sincronizacion.
- Se agrego el comando `sync_soft_deleted_operational_state` para corregir filas legacy que quedaron inconsistentes.
- El backfill ahora invalida los caches alcanzados por soft-delete sin reemitir side effects externos como remociones hacia Gestionar.

## Decision y supuesto

- El estado operativo sincronizado queda declarado por modelo via `SOFT_DELETE_OPERATIONAL_UPDATES` y `SOFT_RESTORE_OPERATIONAL_UPDATES`.
- En modelos VAT basados en `estado`, el restore vuelve a un estado operativo base (`planificado/planificada`) y no intenta reconstruir el estado exacto previo al delete.
- `Voucher` queda fuera de este primer corte porque su cancelacion tiene flujo propio de negocio y auditoria, y no es equivalente a un soft-delete.

## Validacion

- `docker compose exec -T django pytest tests/test_soft_delete_flows.py tests/test_soft_delete_state_sync_command.py tests/test_relevamientos_service_unit.py -q`: `40 passed`.
- `docker compose exec -T django pytest VAT/tests.py -k "soft_delete_directo_de_comision_curso_cierra_estado or restore_directo_de_comision_curso_recupera_estado_operativo or soft_delete_cascade_de_curso_cierra_comisiones_hijas or restore_cascade_de_curso_recupera_estados_operativos or soft_delete_cascade_de_oferta_institucional_cancela_estado_y_cierra_comision or restore_cascade_de_oferta_institucional_recupera_estados_operativos or soft_delete_directo_de_comision_cierra_estado" -q`: `7 passed, 92 deselected`.
- `docker compose exec -T django pytest comedores/tests.py -k "relevamiento_create_edit_ajax_editar_rechaza_payload_vacio or relevamiento_create_edit_ajax_editar_rechaza_json_no_objeto" -q`: `2 passed, 63 deselected`.
- `docker compose exec -T django pytest tests/test_soft_delete_flows.py tests/test_soft_delete_state_sync_command.py tests/test_relevamientos_service_unit.py VAT/tests.py comedores/tests.py -k "sync_soft_deleted_operational_state or restore_reactiva_activo or restore_directo_de_comision_curso_recupera_estado_operativo or restore_cascade_de_curso_recupera_estados_operativos or restore_cascade_de_oferta_institucional_recupera_estados_operativos or soft_delete_directo_de_comision_curso_cierra_estado or soft_delete_cascade_de_curso_cierra_comisiones_hijas or soft_delete_cascade_de_oferta_institucional_cancela_estado_y_cierra_comision or soft_delete_directo_de_comision_cierra_estado or update_territorial or relevamiento_create_edit_ajax_editar_rechaza_payload_vacio or relevamiento_create_edit_ajax_editar_rechaza_json_no_objeto" -q`: `17 passed, 187 deselected`.
- `docker compose exec -T django black core/soft_delete/state_sync.py core/soft_delete/base.py core/soft_delete/cascade.py core/management/commands/sync_soft_deleted_operational_state.py VAT/models.py ciudadanos/models.py centrodefamilia/models.py relevamientos/service.py tests/test_soft_delete_flows.py tests/test_soft_delete_state_sync_command.py VAT/tests.py tests/test_relevamientos_service_unit.py comedores/tests.py scripts/ci/pr_lint_tools.py`: sin cambios pendientes de formato despues del ultimo ajuste.
- `docker compose exec -T django pylint core/soft_delete/state_sync.py core/soft_delete/base.py core/soft_delete/cascade.py core/management/commands/sync_soft_deleted_operational_state.py relevamientos/service.py VAT/cache_utils.py --rcfile=.pylintrc`: `10.00/10`.
- `docker compose exec -T django python -m py_compile scripts/ci/pr_lint_tools.py`: sin errores.
- `docker compose exec -T django python manage.py check`: `System check identified no issues (0 silenced)`.
