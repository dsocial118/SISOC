# Centro detalle: filtro y paginación de planes curriculares

Fecha: 2026-04-06

## Cambio aplicado

En la pestaña `#cursos` del detalle de centros (`/vat/centros/<id>/`) se ajusto el bloque `Planes Curriculares` para:

- filtrar por texto sobre nombre del plan, titulo asociado, sector, subsector, modalidad y normativa;
- paginar resultados de a 20 registros por pagina;
- mantener la navegacion dentro de la pestaña `#cursos` al filtrar o paginar.

## Archivos involucrados

- `VAT/views/centro.py`
- `VAT/templates/vat/centros/centro_detail.html`
- `VAT/tests.py`

## Validacion

Se agrego un test de regresion para cubrir filtro y paginacion del listado de planes curriculares dentro del detalle del centro.