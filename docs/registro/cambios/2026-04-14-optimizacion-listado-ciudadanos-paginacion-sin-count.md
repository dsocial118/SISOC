# Optimización de `/ciudadanos/listar`

## Qué cambió

- El listado de ciudadanos dejó de usar `COUNT(*)` exacto para paginar.
- Se removió el ordenamiento alfabético costoso del queryset del listado y se reemplazó por un orden estable por `pk`.
- Se agregaron índices compuestos para acompañar el patrón real de acceso del listado y de la búsqueda por documento con soft delete.
- La grilla ahora pagina en dos pasos: primero obtiene solo `ids` de la página y luego hidrata únicamente las 25 filas visibles.
- El listado dejó de hacer `select_related` de `municipio` y `localidad`; solo trae `sexo` y `provincia`, que son las relaciones renderizadas.
- El queryset del listado usa `only(...)` para limitar columnas a las que realmente consume la tabla.
- El filtro de provincias usa choices cacheados para no reconstruir la lista completa en cada request.
- La búsqueda `q` diferencia entre documento numérico y texto libre, reutilizando el filtro indexable por documento cuando corresponde.

## Motivación

Con una tabla de ciudadanos de gran volumen, el costo dominante del listado venía de:

- contar todos los registros filtrados en cada request,
- ordenar por `apellido, nombre` antes de paginar,
- hidratar relaciones y columnas que la tabla no usa,
- reconstruir la lista de provincias del filtro en cada request,
- consultar siempre sobre filas activas (`deleted_at IS NULL`) sin índices compuestos alineados a ese filtro.

## Impacto esperado

- Menor latencia en la carga inicial y en la paginación de `/ciudadanos/listar`.
- Menor presión sobre MySQL al evitar `COUNT(*)` exactos del universo filtrado.
- Mejor uso de índices para navegación por páginas y filtros frecuentes por provincia/documento.

## Trade-off

- La UI ya no muestra el total exacto de resultados en este listado.
- La paginación conserva navegación incremental por páginas cercanas, pero sin conocer el total final.
