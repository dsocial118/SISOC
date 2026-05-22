# VAT cursos: buscar prioriza cursos marcados como prioritarios

Fecha: 2026-04-21

## Qué se cambió

- Se ajusta el orden base del listado de cursos operativos en `GET /api/vat/cursos/buscar/` para que los cursos con `prioritario = true` aparezcan primero.
- El orden secundario queda en `fecha_creacion` descendente y luego `nombre` ascendente.
- El endpoint `GET /api/vat/cursos/prioritarios/` sigue disponible y reutiliza la misma base ordenada.

## Criterio funcional

- La búsqueda de cursos sigue filtrando por texto y por los filtros existentes.
- Cuando hay cursos prioritarios y no prioritarios en el mismo resultado, los prioritarios se muestran antes.
- El orden secundario entre cursos del mismo grupo mantiene estabilidad por fecha de creación y nombre.

## Validación

- Se agrega un test de regresión para verificar que el endpoint `buscar` devuelve primero los cursos prioritarios.