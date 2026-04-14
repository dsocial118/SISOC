# Optimización de `/ciudadanos/listar`

## Qué cambió

- El listado de ciudadanos dejó de usar `COUNT(*)` exacto para paginar.
- Se removió el ordenamiento alfabético costoso del queryset del listado y se reemplazó por un orden estable por `pk`.
- Se agregaron índices compuestos para acompañar el patrón real de acceso del listado y de la búsqueda por documento con soft delete.

## Motivación

Con una tabla de ciudadanos de gran volumen, el costo dominante del listado venía de:

- contar todos los registros filtrados en cada request,
- ordenar por `apellido, nombre` antes de paginar,
- consultar siempre sobre filas activas (`deleted_at IS NULL`) sin índices compuestos alineados a ese filtro.

## Impacto esperado

- Menor latencia en la carga inicial y en la paginación de `/ciudadanos/listar`.
- Menor presión sobre MySQL al evitar `COUNT(*)` exactos del universo filtrado.
- Mejor uso de índices para navegación por páginas y filtros frecuentes por provincia/documento.

## Trade-off

- La UI ya no muestra el total exacto de resultados en este listado.
- La paginación conserva navegación incremental por páginas cercanas, pero sin conocer el total final.
