# Detalle de parametría de vouchers: filtro y paginación

Fecha: 2026-04-06

## Cambio aplicado

En la vista de detalle de parametria de vouchers (`/vat/vouchers/parametrias/<id>/`) se ajusto la tabla `Vouchers asignados` para:

- paginar resultados de a 20 registros por pagina;
- permitir busqueda por ciudadano usando nombre, apellido o DNI;
- conservar los contadores generales de la parametria sobre el total de vouchers, sin afectar esos metricos por el filtro de tabla.

## Archivos involucrados

- `VAT/views/voucher_parametria.py`
- `VAT/templates/vat/voucher/parametria_detail.html`
- `VAT/tests.py`

## Validacion

Se agrego un test de regresion para filtro y paginacion del detalle.

No fue posible ejecutar `docker compose exec -T django pytest -n auto VAT/tests.py -k voucher_parametria_detail_filters_and_paginates_vouchers` en este entorno porque Docker Desktop no estaba disponible (`open //./pipe/dockerDesktopLinuxEngine: The system cannot find the file specified`).