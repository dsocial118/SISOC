# VAT Web - actualización de Swagger y colección Postman

Fecha: 2026-04-02

## Qué cambió

- Se enriqueció la documentación OpenAPI de VAT Web con `summary` y ejemplos de respuesta para:
  - `GET /api/vat/web/centros/`
  - `GET /api/vat/web/titulos/`
  - `GET /api/vat/web/cursos/`
- Se amplió la colección `postman/VAT Web - Sectores Subsectores Cursos.postman_collection.json`.
- La colección ahora incluye requests para:
  - centros,
  - flujo sector -> subsector -> cursos,
  - filtros adicionales de cursos,
  - consulta de inscripciones,
  - alta de inscripción por documento.

## Objetivo

Mantener alineados Swagger VAT (`/api/docs/VAT/`) y la colección Postman con el contrato vigente de VAT Web.

## Validación prevista

- Regenerar/validar schema con `manage.py spectacular --validate`.
- Verificar que la colección Postman importe correctamente y que el JSON sea válido.