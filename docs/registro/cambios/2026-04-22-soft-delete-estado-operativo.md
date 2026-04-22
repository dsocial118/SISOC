# Soft-delete y estado operativo

Fecha: 2026-04-22

## Que se resolvio

- Se corrigio la desincronizacion entre `deleted_at` y el estado operativo en entidades con soft-delete.
- Antes, el soft-delete marcaba la baja logica pero no siempre dejaba consistente `activo` o `estado`.

## Cambio aplicado

- `core.soft_delete` ahora sincroniza `activo=False` cuando el modelo expone ese campo.
- Se agregaron mappings explicitos en VAT para `Curso`, `ComisionCurso`, `OfertaInstitucional` y `Comision`.
- Las cascadas quedan cubiertas por la misma logica de sincronizacion.
- Se agrego el comando `sync_soft_deleted_operational_state` para corregir filas legacy que quedaron inconsistentes.

## Decision y supuesto

- `restore()` no reactiva automaticamente el estado operativo previo.
- `Voucher` queda fuera de este primer corte porque su cancelacion tiene flujo propio de negocio y auditoria, y no es equivalente a un soft-delete.

## Validacion

- `docker compose exec -T django pytest tests/test_soft_delete_state_sync_command.py -q`: `2 passed`.
- `docker compose exec -T django pytest tests/test_soft_delete_flows.py tests/test_soft_delete_state_sync_command.py VAT/tests.py -k "emitir_post_soft_delete or reactiva_activo or soft_delete_directo_de_comision_curso_cierra_estado or soft_delete_cascade_de_curso_cierra_comisiones_hijas or soft_delete_cascade_de_oferta_institucional_cancela_estado_y_cierra_comision or soft_delete_directo_de_comision_cierra_estado or sync_soft_deleted_operational_state" -q`: `8 passed, 103 deselected`.
- `docker compose exec -T django black ... --config pyproject.toml`: formateo aplicado sobre los archivos Python modificados.
- `docker compose exec -T django pylint core/soft_delete/base.py core/soft_delete/cascade.py core/soft_delete/state_sync.py core/management/commands/sync_soft_deleted_operational_state.py VAT/models.py --rcfile=.pylintrc`: sin findings funcionales nuevos; quedaron un `too-many-locals` preexistente en `core/soft_delete/cascade.py` y warnings de line endings mixtos en `VAT/models.py`.
- `docker compose exec django python manage.py check`: `System check identified no issues (0 silenced)`.
