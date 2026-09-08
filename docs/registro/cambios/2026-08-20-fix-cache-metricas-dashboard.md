# Dashboard: invalidación de caché al actualizar métricas

## Contexto

La suite completa detectó que las señales de Comedores recalculaban el Dashboard
usando valores de presupuesto previamente cacheados. Si primero se creaba un
comedor, los presupuestos quedaban cacheados en cero y la creación posterior de
`ValorComida` no actualizaba esos importes.

## Cambio

Antes de regenerar las métricas persistidas se invalidan exclusivamente las cinco
claves de caché del Dashboard. La siguiente lectura reconstruye cantidad de
comedores, relevamientos y presupuestos desde las proyecciones públicas de dominio.

No se limpia la caché global ni se modifican contratos de Comedores o
Relevamientos.

## Validación

- `tests/test_dashboard_comedores_core_boundary.py`
- Suite completa de `pytest`.
