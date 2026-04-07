# 2026-04-06 - Coleccion Postman VAT operativa

## Resumen

Se agrego una coleccion de Postman orientada a consumo operativo de VAT para recorrer:

- planes curriculares,
- centros,
- cursos por centro,
- comisiones de curso por curso.

## Archivo agregado

- `postman/VAT - Planes Centros Cursos Comisiones.postman_collection.json`

## Alcance

La coleccion usa endpoints de `api/vat/` protegidos con API key y deja variables de coleccion para encadenar el flujo:

- `sector_id`
- `plan_id`
- `centro_id`
- `curso_id`

## Notas

- Para autenticacion, la cabecera esperada es `Authorization: Api-Key <clave>`.
- Se dejo separado de la coleccion VAT Web porque los endpoints web no cubren planes curriculares ni comisiones de curso operativas.