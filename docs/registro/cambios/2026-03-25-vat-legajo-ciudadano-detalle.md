# VAT en legajo de ciudadano

Fecha: 2026-03-25

## Qué cambió

- Se completó la pestaña `VAT` del legajo de ciudadano en `ciudadanos/ver/<id>`.
- El detalle ahora se agrupa por programa e informa:
  - voucher asignado,
  - créditos totales,
  - créditos actuales,
  - cursos asignados,
  - asistencia acumulada.
- También se muestran las inscripciones del ciudadano con acceso al detalle de inscripción, comisión y voucher cuando existe.
- Se corrigió el alta de `Inscripcion` VAT para que, cuando la oferta usa voucher, el débito se aplique también en el flujo de comisión usando el costo de la oferta.

## Alcance

- Cambio localizado al legajo de ciudadano.
- Sin cambios de modelo ni migraciones.
- Se reutilizó la información ya disponible en VAT (`Inscripcion`, `InscripcionOferta`, `Voucher`, `AsistenciaSesion`).
- Se agregó débito reutilizable en `VoucherService` para mantener consistente el saldo visible del voucher.

## Validación prevista

- Verificar manualmente `http://localhost:8001/ciudadanos/ver/1` en la pestaña `VAT`.
- Ejecutar tests unitarios de `ciudadanos`.
