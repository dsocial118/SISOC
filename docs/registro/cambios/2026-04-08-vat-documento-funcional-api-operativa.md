# 2026-04-08 - Documento funcional de API operativa VAT

## Resumen

Se agrego un documento funcional para describir qué datos de negocio expone la API operativa de VAT en el flujo de planes curriculares, centros, cursos y comisiones.

## Archivo agregado

- `docs/vat/documento-funcional-api-vat-planes-centros-cursos-comisiones.md`

## Alcance

- El documento se enfoca en el valor funcional de los datos disponibles al consumir `/api/vat/`.
- No describe la colección Postman como herramienta ni su uso paso a paso.
- Ordena el flujo funcional en cinco niveles: ubicacion, planes, centros, cursos y comisiones.

## Notas

- El contenido toma como referencia la coleccion `postman/VAT - Planes Centros Cursos Comisiones.postman_collection.json`.
- Los campos documentados se alinean con serializers y filtros vigentes en `VAT/api_views.py` y `VAT/serializers.py`.