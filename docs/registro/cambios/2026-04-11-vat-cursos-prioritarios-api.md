# Cursos prioritarios en API VAT

Fecha: 2026-04-11

## Qué se cambió

- Se agrega el campo booleano `prioritario` en `VAT.Curso` para marcar cursos prioritarios desde base de datos.
- Se expone `prioritario` en las respuestas de cursos operativos.
- Se agrega `GET /api/vat/cursos/prioritarios/` con el mismo payload enriquecido del buscador de cursos.
- El endpoint devuelve solo cursos prioritarios activos que tengan al menos una comisión activa.
- Se agrega el request correspondiente en la colección Postman `VAT - Planes Centros Cursos Comisiones`.

## Criterio funcional

- Un curso prioritario es un curso operativo marcado explícitamente en la base con `prioritario = true`.
- El endpoint de prioritarios reutiliza la misma estructura enriquecida del buscador: centro con provincia anidada, bloque `ciudad` con provincia/municipio/localidad/dirección, programa derivado, parametrías de voucher, comisiones, horarios, sesiones y cupos.
- El endpoint admite los filtros ya soportados por `CursoViewSet` porque reutiliza el mismo queryset base filtrado.
- El resultado queda restringido a opciones vigentes de inscripción: curso activo y al menos una comisión activa.
- Si un curso prioritario tiene múltiples comisiones activas, la paginación devuelve el curso una sola vez y mantiene la lista de comisiones activas en el payload enriquecido.

## Validación

- Se agrega test automático para verificar que:
  - el endpoint devuelve solo cursos prioritarios,
  - la respuesta conserva el payload enriquecido esperado.
