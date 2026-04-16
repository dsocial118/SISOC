# 2026-03-31 - VAT: corrección del alta de Voucher en el admin

## Contexto

El smoke test de URLs detectó un `500` en `/admin/VAT/voucher/add/`. El error venía del `VoucherAdmin`, que incluía `fecha_asignacion` en el formulario de alta aunque el campo es `auto_now_add` y Django no lo puede editar.

## Cambios aplicados

- `VAT/admin.py`
  - Se agregó `fecha_asignacion` a `readonly_fields` en `VoucherAdmin`.
  - Se mantiene visible en el admin, pero fuera del formulario editable.

- `tests/test_vat_admin_unit.py`
  - Se agregó una regresión que verifica que el alta del admin de Voucher responde `200`.

## Impacto esperado

- El admin de Voucher deja de romperse en GET `/admin/VAT/voucher/add/`.
- El smoke test de URLs no debería volver a fallar por este `FieldError`.

## Validación

- Pendiente de ejecutar en este entorno.
- Comando sugerido:
  - `LOG_DIR=/tmp/sisoc-logs PYTEST_RUNNING=1 python -m pytest -q tests/test_vat_admin_unit.py tests/test_urls_no_500.py -k 'VAT_voucher_add'`

## Riesgos y rollback

- Riesgo bajo: el campo `fecha_asignacion` pasa a ser solo lectura en admin, que coincide con su naturaleza de sistema.
- Rollback: revertir `VAT/admin.py`, `tests/test_vat_admin_unit.py` y este documento.
