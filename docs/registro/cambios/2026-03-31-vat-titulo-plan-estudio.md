# VAT: Titulo de Referencia sin sector/subsector propios

Fecha: 2026-03-31

## Cambio

Se eliminan `sector` y `subsector` de `TituloReferencia`.

La clasificación académica queda centralizada en `PlanVersionCurricular` (`Plan de Estudio`), y `TituloReferencia` pasa a depender de `plan_estudio` para esa información.

## Impacto

- Formularios de título: ya no muestran sector ni subsector.
- Tablas y detalle de títulos: muestran `Plan de Estudio` en lugar de sector/subsector propios.
- API de títulos: deja de exponer `sector` y `subsector` como campos propios del título.
- Se agrega migración para remover `sector_id` y `subsector_id` de `VAT_tituloreferencia`.

## Compatibilidad

Filtros por `sector_id` y `subsector_id` en endpoints de títulos se resuelven ahora a través de `plan_estudio__sector` y `plan_estudio__subsector`.