# 2026-04-06 - Optimizacion de performance en detalle de centro VAT

## Contexto
- El acceso a `vat/centros/<pk>/` estaba cargando demasiados datos y formularios pesados en el primer request.
- En produccion, el volumen de cursos, comisiones y planes curriculares volvia lenta la entrada al detalle del centro.

## Cambios aplicados
- Se redujo el contexto inicial de `CentroDetailView` a los datos visibles de la solapa general y a contadores livianos.
- Se movio el contenido pesado de cursos/comisiones/planes a un endpoint parcial nuevo: `vat/centros/<pk>/panel/cursos/`.
- Se agrego carga diferida de la solapa `#cursos`, con fetch al abrirla y navegacion AJAX para filtro y paginacion del panel.
- Se agrego cache paginado para planes curriculares por provincia/busqueda/pagina.
- Se optimizaron queries del panel de cursos con `annotate`, `select_related` y `prefetch_related`.
- Se agrego un indice compuesto sobre `PlanVersionCurricular(provincia, activo)`.
- Se ajustaron tests para cubrir el nuevo contrato entre vista detalle liviana y panel parcial pesado.

## Impacto esperado
- El primer render del detalle de centro deja de arrastrar el costo de cursos, comisiones y catalogos.
- La UI se mantiene igual, salvo que la solapa `#cursos` ahora se completa al abrirse.
- El filtro y la paginacion de planes dentro de la solapa siguen disponibles, pero sin exigir un render completo del detalle.

## Validacion
- Se actualizaron tests puntuales en `VAT/tests.py` para el render inicial liviano y para el endpoint parcial de cursos.
- Queda pendiente ejecutar la suite en un entorno con dependencias del proyecto disponibles.

## Riesgos y rollback
- Riesgo principal: errores de inicializacion JS en la solapa diferida si cambia el markup de los modales o tablas.
- Rollback: revertir la vista parcial, el lazy-load del template y la migracion del indice.
