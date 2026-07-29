# Reintegro de voucher al rechazar una inscripción VAT

Fecha: 2026-07-29

## Contexto

Una inscripción de curso que usaba voucher podía pasar de un estado con cupo a
`rechazada` sin revertir el débito. Al aceptarla nuevamente, el flujo volvía a
descontar créditos.

## Cambios realizados

- Al rechazar una inscripción que ocupaba cupo se revierte el último débito de
  voucher asociado a esa inscripción.
- La reversión actualiza los saldos, conserva la trazabilidad mediante una
  recarga de compensación y deja el voucher activo si se había agotado.
- Al volver a aceptar una inscripción se evita un nuevo débito si ya existe un
  débito vigente histórico para ella.
- Se agregaron regresiones del cambio de estado por lote para ambos ciclos.

## Impacto

- El saldo del voucher coincide con el estado final de la inscripción.
- La compensación queda auditada en `VoucherRecarga` y `VoucherLog`.
- No se altera el comportamiento de vouchers vencidos o cancelados.
