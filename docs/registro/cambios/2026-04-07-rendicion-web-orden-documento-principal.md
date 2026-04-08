# Rendicion web: documento principal correcto en categorias con historial

## Contexto

En `Comprobantes` y `Documentacion Extra`, el detalle web podia seguir
mostrando como principal un archivo viejo en `A Subsanar` aunque el usuario ya
hubiera cargado una nueva subsanacion. Eso generaba confusion porque el
documento observado seguia apareciendo arriba y en rojo, mientras el archivo
nuevo quedaba mezclado en historial.

## Cambio realizado

- La logica de detalle para categorias con historial ahora toma como documento
  principal el ultimo archivo cargado de la cadena.
- Los documentos anteriores pasan a `subsanaciones_historial`, ordenados de mas
  nuevo a mas viejo.
- Con esto, si existe una nueva subsanacion presentada o validada, el archivo
  viejo observado deja de quedar primero en la lista.

## Validacion

- `docker compose exec django pytest tests/test_rendicioncuentasmensual_services_unit.py -q`
