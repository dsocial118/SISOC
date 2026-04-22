# Ejemplos Postman y Swagger para cursos VAT

Fecha: 2026-04-12

## Qué se cambió

- Se crea la colección Postman `VAT - Cursos Busqueda y Prioritarios` con ejemplos específicos para:
  - `GET /api/vat/cursos/buscar/`
  - `GET /api/vat/cursos/prioritarios/`
- La colección incluye casos de primera carga sin texto, casos felices, filtros combinados y errores esperados para el buscador.
- Se corrige el bloque de cursos en la colección existente `VAT - Planes Centros Cursos Comisiones` para que los requests `Buscar cursos por texto` y `Listar cursos prioritarios` queden separados correctamente.
- Se actualiza Swagger/OpenAPI en `VAT/api_views.py` con:
  - ejemplos de respuesta,
  - documentación de filtros opcionales compartidos,
  - descripciones con URLs de uso reales.

## Criterio funcional

- La colección nueva está pensada como material de prueba y referencia rápida para integraciones y QA.
- Swagger ahora expone mejor el contrato operativo real de ambos endpoints, incluyendo primera carga paginada, filtros y errores frecuentes.
- Swagger ahora también deja explícito que ambos endpoints muestran solo cursos activos con comisiones activas.

## Validación

- Se validó que `api_views.py` no tenga errores de análisis.
- Se validó que ambas colecciones Postman queden sin errores de estructura.
- Se reejecuta el subset de tests de cursos VAT para asegurar que los cambios de documentación no afecten la carga del módulo.