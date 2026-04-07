# 2026-04-07 - Fix endpoint API VAT centros y validacion Postman

## Resumen

Se corrigio el serializer de `api/vat/centros/`, que estaba declarando campos inexistentes del modelo `Centro` y provocaba error 500 al listar centros con API key valida.

## Cambios

- Se removieron del serializer los campos inexistentes `modalidad_institucional`, `modalidad_institucional_nombre` y `fecha_alta`.
- Se agregaron tests API de regresion para:
  - `GET /api/vat/centros/`
  - `GET /api/vat/cursos/?centro_id=...`
  - `GET /api/vat/comisiones-curso/?curso_id=...`
- Se agrego a la coleccion Postman un request inicial de validacion sobre `planes-curriculares` para comprobar autenticacion y disponibilidad antes del flujo completo.
- Se agregaron variables `provincia_id` y `municipio_id` y requests auxiliares de ubicacion para encadenar `provincia -> municipio -> centro -> curso -> comision`.
- Se agregaron filtros geograficos directos `provincia_id` y `municipio_id` en `GET /api/vat/cursos/` y `GET /api/vat/comisiones-curso/`.

## Impacto

- La API key ya autenticaba correctamente; el problema real era un bug interno del endpoint de centros.
- Con este ajuste, el flujo operativo de Postman queda alineado con endpoints efectivamente utilizables.