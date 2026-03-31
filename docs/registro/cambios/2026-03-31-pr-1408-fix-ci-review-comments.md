## Contexto

Correccion acotada sobre el trabajo acumulado en `development` que alimenta el PR `#1408` hacia `main`.
El objetivo fue atender hallazgos del review con impacto potencial en CI o en errores de ejecucion temprana.

## Cambios realizados

- Se agrego un shim minimo en `VAT/services/oferta_service/impl.py` para evitar errores de importacion del paquete `VAT.services.oferta_service` mientras persisten imports legacy.
- `VAT/services/inscripcion_service.py` ahora importa `VoucherService` desde el export publico del paquete y valida que el costo de una oferta con voucher sea un entero exacto de creditos antes de debitar.
- `VAT/management/commands/recargar_vouchers.py` dejo de depender de `django.contrib.auth.models.User` y resuelve el modelo con `get_user_model()`.
- Se corrigieron dos detalles de UI/documentacion detectados en review:
  - clase base `bi` faltante en `VAT/templates/vat/institucion/ubicacion_detail.html`
  - texto `Nuevo Resultado` en `VAT/templates/vat/evaluacion/resultado_form.html`
  - docstring consistente en `VAT/services/sesion_comision_service/impl.py`
- Se agrego cobertura de regresion para rechazar costos decimales en el debito de voucher.

## Decision clave

No se revirtio el cambio en `VAT/migrations/0001_initial.py` dentro de esta tarea.
Aunque editar una migracion historica no es ideal, en este caso la modificacion parece responder a compatibilidad de instalaciones nuevas sobre MySQL; moverlo a una migracion posterior no evita el fallo inicial en entornos frescos.

## Riesgo / seguimiento

- El shim de `OfertaService` es deliberadamente defensivo: evita el import error, pero mantiene el fallo explicito si alguien intenta instanciar el servicio legacy.
- Si a futuro VAT admite costos de voucher con decimales reales, habra que redisenar `Voucher` y `VoucherService` para operar con `Decimal` end-to-end.
