# Timeout en listado de responsables CDF

## Contexto

Al abrir `/beneficiarios/responsables/` el listado podia terminar en 502 luego de
una espera prolongada. La vista usaba el paginador exacto de Django sobre un
queryset anotado con `Count("beneficiarios")`, lo que fuerza un conteo global
con join/group antes de renderizar una pagina de 10 filas.

## Cambio

- La vista de responsables usa `NoCountPaginator`.
- La paginacion trabaja primero sobre IDs y evita el `COUNT(*)` exacto.
- La cantidad de beneficiarios se calcula solo al hidratar los responsables
  visibles.
- Si el usuario filtra explicitamente por `cantidad_beneficiarios`, se mantiene
  la anotacion necesaria para respetar ese filtro.

## Impacto

El acceso normal al listado deja de depender de un conteo global caro y conserva
la columna visible de cantidad de beneficiarios para las filas renderizadas.
