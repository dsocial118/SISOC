# 2026-04-06 - Carga diferida del panel de cursos en detalle de centro VAT

## Estado
- aceptada

## Contexto
- El detalle de centro estaba resolviendo en el primer request datos que solo se usan al abrir la solapa `#cursos`.
- El cuello de botella principal no estaba en la UI sino en el costo acumulado de queries, formularios y tablas que no eran visibles al entrar.

## Decision
- Mantener la UI actual del detalle de centro, pero cargar la solapa `#cursos` en forma diferida mediante un endpoint parcial dedicado.
- Conservar filtro y paginacion sobre el panel, usando mejora progresiva: con JS activo se resuelve via fetch; sin JS sigue funcionando por recarga completa.
- Aplicar cache solo al subconjunto mas costoso y estable del panel: la lista paginada de planes curriculares filtrados por provincia/busqueda.

## Consecuencias
- El tiempo de entrada al detalle mejora porque el request inicial deja de construir el panel pesado.
- Se agrega complejidad moderada en frontend por la re-inicializacion de modales y handlers despues del fetch.
- El contrato de testing cambia: el detalle valida placeholder y bootstrap de la solapa; el contenido pesado se valida en la vista parcial.

## Referencias
- `VAT/views/centro.py`
- `VAT/templates/vat/centros/centro_detail.html`
- `VAT/templates/vat/centros/partials/centro_cursos_panel.html`
