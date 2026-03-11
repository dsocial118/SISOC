# 2026-03-12 - Fix filtro por DNI en nómina global

## Contexto
- En la vista de nómina del legajo de comedor, la búsqueda se hacía en frontend sobre las filas renderizadas.
- Eso provocaba que el filtro aplicara solo a la página actual, sin incluir coincidencias en otras páginas de la nómina.

## Cambios aplicados
- Se movió el filtro por DNI al backend en la vista de detalle de nómina:
  - `NominaDetailView` ahora lee `dni` por query string y lo pasa a `ComedorService.get_nomina_detail(...)`.
- Se extendió `ComedorService.get_nomina_detail` para aceptar `dni_query` y filtrar el queryset de nómina antes de paginar.
- Se agregó helper interno `_apply_nomina_dni_filter(...)` con validación básica (solo dígitos).
- Se ajustó `templates/comedor/nomina_detail.html`:
  - la barra de búsqueda ahora es un formulario GET por `dni`.
  - la paginación preserva el parámetro `dni`.
  - se agregó acción para limpiar el filtro.
- Se removió el filtrado client-side de filas en `static/custom/js/nomina_detail.js` para evitar comportamiento inconsistente con paginación.
- Se agregó test de regresión para validar que el filtro encuentra registros fuera de la página actual.

## Impacto esperado
- La búsqueda por DNI en la nómina devuelve coincidencias del listado completo del espacio/admisión, independientemente de la página actual.
- Se mantiene el comportamiento de estadísticas generales de la nómina (no se recalculan en base al filtro).

## Validación
- `docker compose exec django pytest -q tests/test_nomina_views_unit.py::test_nomina_detail_context_data comedores/tests.py::test_nomina_detail_view_filtra_por_dni_en_toda_la_nomina tests/test_comedor_service_characterization_db.py::test_get_nomina_detail_con_db_real_calcula_resumen_y_rangos`
- Resultado: `3 passed`.

## Riesgos y rollback
- Riesgo bajo: cambio acotado al flujo de visualización de nómina.
- Rollback: revertir los cambios en vista/servicio/template/js y el test asociado.
