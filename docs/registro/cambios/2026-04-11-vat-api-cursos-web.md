# Corrección de API VAT para cursos operativos

Fecha: 2026-04-11

## Problema

- La operación real de VAT usa `Curso` y `ComisionCurso`.
- Los endpoints web y parte del swagger seguían exponiendo `Comision` y `OfertaInstitucional`, modelos que hoy no representan el flujo operativo vigente para cursos con voucher.

## Cambios realizados

- `GET /api/vat/web/cursos/` pasa a listar `ComisionCurso`.
- `POST /api/vat/web/inscripciones/` pasa a validar y crear inscripciones sobre `ComisionCurso`.
- `POST /api/vat/inscripciones/` ahora acepta tanto `comision` como `comision_curso`.
- Se agrega `POST /api/vat/inscripciones-curso/` como endpoint explícito para comisiones de curso en swagger.
- Se refuerza la documentación OpenAPI de `GET /api/vat/cursos/`, `GET /api/vat/comisiones-curso/` y `POST /api/vat/inscripciones-curso/` para dejar explícito en Swagger que el flujo operativo vigente de cursos usa `Curso` y `ComisionCurso`, y que `comisiones` queda como ruta legacy de oferta institucional.

## Criterio funcional

- Flujo web voucher: debe usar `ComisionCurso`.
- Listado de cursos disponible para frontend: debe usar `ComisionCurso`.
- `Comision` y `InscripcionOferta` quedan como capa separada para la línea de oferta institucional legacy, sin mezclarse con la operación real de cursos VAT.