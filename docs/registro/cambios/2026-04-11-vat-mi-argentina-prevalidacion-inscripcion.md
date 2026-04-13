# Flujo Mi Argentina para inscripción VAT Web

Fecha: 2026-04-11

## Qué se cambió

- Se agrega `POST /api/vat/web/inscripciones/prevalidar/` para consultar elegibilidad antes de crear la inscripción.
- La prevalidación usa la lógica real de SISOC para curso, comisión, cupo, voucher, parametrías e inscripción única activa.
- Se mantiene `POST /api/vat/web/inscripciones/` como confirmación final del alta.
- Se documenta el flujo completo Mi Argentina -> SISOC en `docs/vat/documento-funcional-mi-argentina-inscripcion-vat.md`.

## Criterio funcional

- Mi Argentina autentica e identifica.
- SISOC valida e inscribe.
- Las reglas de voucher y elegibilidad no se replican fuera del backend.

## Validación

- Se agregan tests automáticos para:
  - prevalidación sin voucher activo,
  - flujo completo centro -> cursos -> prevalidación -> inscripción -> consulta final.