# 2026-04-07 - VAT centro cursos: invalidacion de cache del panel

## Contexto
- Los tests del panel de cursos de centros VAT fallaban de forma intermitente cuando un request previo dejaba cacheada una combinacion de provincia, busqueda y pagina sin planes curriculares.
- El panel `vat_centro_cursos_panel` reutilizaba esa entrada aunque despues se crearan planes nuevos en la misma provincia, por lo que el listado quedaba vacio hasta que expirara el TTL.

## Cambio aplicado
- Se versiono la clave de cache de `planes_centro` en `VAT/views/centro.py`.
- La clave de cache del panel ahora tambien discrimina por `sector_id` para no mezclar resultados entre filtros distintos.
- Se agrego `VAT/cache_utils.py` para centralizar la version del cache y bumppearla cuando cambian `PlanVersionCurricular` o `TituloReferencia`.
- Se cargo ese registro de señales desde `VAT/apps.py`.
- Se preserva `sector_id` en la paginacion del parcial `vat_centro_cursos_panel` para no perder el filtro al navegar entre paginas.
- Se agregaron tests de regresion en `VAT/tests.py` para cubrir el caso: cache vacio primero, alta de plan despues, y segundo request viendo el plan sin esperar expiracion; y otro caso donde el filtro por sector no debe reutilizar cache de un request previo sin filtro.
- Los tests del panel afectados se ejecutan con un `ROOT_URLCONF` de prueba acotado para no depender del `config.urls` completo durante el subset local.

## Impacto esperado
- El panel de cursos deja de mostrar resultados obsoletos despues de altas/bajas de planes curriculares.
- El filtro por sector en la tabla de Planes Curriculares del detalle de centro deja de comportarse de forma erratica despues de requests previos cacheados.
- La paginacion y el filtro siguen cacheados, pero se invalidan cuando cambia el catalogo relevante y ya no pierden el `sector_id` al navegar.

## Validacion
- `pytest VAT/tests.py -k "test_centro_cursos_panel_renderiza_accion_para_crear_curso_desde_plan_curricular or test_centro_cursos_panel_filtra_y_pagina_planes_curriculares or test_centro_cursos_panel_invalida_cache_al_crear_planes" -vv`
- Validacion local realizada con `USE_SQLITE_FOR_TESTS=1` y el virtualenv compartido del repo.
