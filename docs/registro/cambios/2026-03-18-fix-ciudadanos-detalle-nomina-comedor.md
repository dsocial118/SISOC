# Fix detalle de ciudadano con nómina de comedor

## Contexto

En `ciudadanos/ver/<pk>` el detalle del ciudadano fallaba al intentar cargar el bloque de comedor.

La causa raíz era una query desactualizada en `CiudadanosDetailView.get_comedor_context`: el modelo `Nomina` ya no tiene relación directa con `comedor` desde la migración que movió ese vínculo a `admision`.

## Cambio aplicado

- Se corrigió el `select_related` de `Nomina` para navegar por `admision__comedor__...`.
- Se endureció el test unitario de `ciudadanos.views` para que falle si se reintroduce el acceso legacy por `comedor__...`.

## Motivo

El fix mantiene el comportamiento esperado del detalle de ciudadano y alinea la vista con el esquema actual del dominio de comedores, evitando un `FieldError` en tiempo de ejecución.
