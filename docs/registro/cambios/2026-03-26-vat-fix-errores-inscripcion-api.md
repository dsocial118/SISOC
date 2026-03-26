# 2026-03-26 - VAT: correcciones críticas en alta de inscripciones API

## Contexto

Durante la revisión del PR 1341 se detectaron dos riesgos críticos:
- el alta web de inscripciones devolvía `500` ante errores de negocio (`ValueError`);
- el alta en `InscripcionViewSet` no usaba `InscripcionService`, omitiendo reglas transaccionales y de voucher.

## Cambios implementados

- `VAT/api_web_views.py`
  - `VatWebInscripcionViewSet.create` ahora captura `ValueError` del serializer/service y lo convierte a `ValidationError` (`400`).

- `VAT/api_views.py`
  - `InscripcionViewSet.perform_create` ahora delega en `InscripcionService.crear_inscripcion`.
  - Se captura `ValueError` y se devuelve `ValidationError` (`400`) en lugar de error interno.

## Cobertura de regresión agregada

- `tests/test_vat_api_web_unit.py`
  - caso que valida `400` al fallar una regla de negocio en alta web.

- `tests/test_vat_api_views_unit.py`
  - caso que verifica delegación a `InscripcionService` desde `InscripcionViewSet`.
  - caso que verifica mapeo de `ValueError` a `ValidationError`.

## Impacto esperado

- Consistencia de comportamiento entre endpoints web/backoffice para altas de inscripción.
- Menor riesgo de `500` por validaciones de negocio esperables.
- Reaprovechamiento de validaciones existentes del service (inscripción única, voucher, auditoría).
