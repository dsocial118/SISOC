# 2026-04-07 - VAT centro: filtros combinados en planes curriculares

## Contexto
- El panel de `Planes Curriculares` en el detalle de centros VAT se volvía difícil de usar cuando la provincia tenía muchos planes activos.
- Hasta ahora solo existían búsqueda por texto, filtro por sector y paginación fija de 20 registros.

## Cambio aplicado
- Se agregaron filtros combinados por `sector`, `subsector` y `modalidad` en el panel `vat_centro_cursos_panel`.
- Se incorporó un selector de cantidad por página con opciones `5`, `10`, `15`, `20`, `50` y `100`, usando `5` como valor por defecto.
- La paginación ahora preserva todos los filtros activos mediante un querystring persistente.
- Se agregó un resumen visual con cantidad de planes por sector dentro del resultado filtrado.
- Se ampliaron los tests en `VAT/tests.py` para cubrir filtros combinados y el selector de tamaño de página.

## Impacto esperado
- En centros con muchas ofertas curriculares, encontrar un plan específico requiere menos scroll y menos cambio de página.
- El usuario puede refinar la tabla de forma incremental sin perder el contexto al paginar.

## Validación
- `docker compose exec -T django pytest VAT/tests.py -k "test_centro_cursos_panel_filtra_y_pagina_planes_curriculares or test_centro_cursos_panel_invalida_cache_al_crear_planes" -vv`