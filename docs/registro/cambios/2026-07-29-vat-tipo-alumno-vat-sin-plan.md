# VAT - Diferenciación de alumnos VAT / Sin Plan en asistencia y exportaciones

## Cambio funcional

Se agrega la clasificación `tipo_alumno` (valores `VAT` / `Sin Plan`) para
distinguir a los alumnos con voucher VAT activo de los que no tienen plan.
La columna "Tipo de alumno" se muestra siempre (aunque todos los alumnos sean
de la misma categoría) en:

- Pantalla de asistencia de sesión (chip destacado para VAT), ambos caminos
  (`ComisionCurso` y legacy `Comision`).
- Detalle de comisión, tabla de inscriptos (pill teal para VAT), ambos caminos.
- Detalle nominal del reporte de inscripciones y asistencia (UI + export
  CSV/Excel), para que la clasificación en pantalla coincida con la exportada.
- Nómina Excel de preinscriptos e inscriptos de comisión de curso.

## Regla de negocio

`Voucher` del ciudadano con `estado="activo"` y `fecha_vencimiento` vigente →
`VAT`; cualquier otro caso → `Sin Plan`. Se chequea la fecha además del estado
porque `vencido` se estampa de forma perezosa al validar vouchers.

El cálculo es exclusivamente backend y está centralizado en
`VAT/services/tipo_alumno_service.py`:

- `anotar_tipo_alumno(inscripciones)`: una sola query por lote para listados
  materializados (views de asistencia, detalle de comisión, nómina Excel).
- `tiene_voucher_activo_subquery()`: `Exists` para querysets en streaming
  (detalle nominal del reporte y sus exports).

## Trade-offs

- Un alumno que pagó con voucher y luego lo agotó (`estado="agotado"`) pasa a
  verse como `Sin Plan`: la regla pedida clasifica por voucher activo hoy, no
  por cómo se pagó la inscripción.
- La columna no participa de búsquedas, ordenamientos ni paginación (que son
  client-side en estas tablas) ni afecta el registro de asistencia.

Tests: `VAT/test_tipo_alumno.py` (servicio, nómina, reporte y renders) y
actualización de asserts de headers/colspans en `VAT/tests.py` y
`VAT/test_comision_detail_template_compartido.py`.
