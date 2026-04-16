# API web VAT

Fecha: 2026-03-25

## Qué cambió

- Se agregaron endpoints de VAT orientados a consumo web en `/api/vat/web/`.
- Se expusieron APIs para centros, títulos, cursos e inscripciones.
- Se documentaron los endpoints con `drf-spectacular` para Swagger.
- Se agregó acceso directo a documentación en `/api/docs/VAT/`, filtrado solo a endpoints de `/api/vat/`.
- La creación de inscripciones vía API reutiliza la lógica de voucher del dominio.

## Endpoints incorporados

- `GET /api/vat/web/centros/`
- `GET /api/vat/web/titulos/`
- `GET /api/vat/web/cursos/`
- `GET /api/vat/web/inscripciones/`
- `POST /api/vat/web/inscripciones/`

## Documentación relacionada

- `docs/vat/api_web.md`

## Validación prevista

- Revisar `/api/docs/` y verificar los tags `VAT Web - *`.
- Probar alta de inscripción con y sin voucher.
