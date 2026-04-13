# 2026-04-06 - Coleccion Postman VAT operativa

## Resumen

Se agrego una coleccion de Postman orientada a consumo operativo de VAT para recorrer:

- planes curriculares,
- centros,
- cursos por centro,
- comisiones de curso por curso.

Luego se amplió con ejemplos concretos de paginacion sobre `GET /api/vat/centros/` para mostrar como leer el total y navegar entre paginas.

## Archivo agregado

- `postman/VAT - Planes Centros Cursos Comisiones.postman_collection.json`

## Alcance

La coleccion usa endpoints de `api/vat/` protegidos con API key y deja variables de coleccion para encadenar el flujo:

- `sector_id`
- `plan_id`
- `centro_id`
- `curso_id`

Tambien incluye ejemplos de consultas paginadas sobre centros para validar:

- `count` como total de registros,
- `results` como pagina actual,
- `next` y `previous` como navegacion.

## Notas

- Para autenticacion, la cabecera esperada es `Authorization: Api-Key <clave>`.
- Se dejo separado de la coleccion VAT Web porque los endpoints web no cubren planes curriculares ni comisiones de curso operativas.