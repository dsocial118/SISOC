# Sistema de benchmark reproducible

## Qué se agregó

- Nuevo comando `python manage.py run_benchmarks`.
- Ejecución segura sobre DB efímera en memoria para no tocar la base local.
- Bootstrap reproducible con migraciones, grupos, permisos y fixtures del repo.
- Runner con comparación contra baseline JSON usando tiempo y cantidad de queries.
- La regresión por tiempo exige delta porcentual y también delta absoluto para evitar falsos positivos en vistas muy rápidas.
- Primer catálogo de escenarios transversales por módulo.

## Decisión principal

Se priorizó reproducibilidad y ejecución automática por Codex sobre fidelidad a producción. Por eso la medición base corre en SQLite efímera y usa baseline versionado del propio repo.

## Observaciones operativas

- El bootstrap tolera una incidencia conocida de `centrodeinfancia/fixtures/departamento_ipi.json` sobre SQLite y la resume en una sola línea para no ensuciar la salida de automatización.
- En esta primera versión la señal fuerte de eficiencia es `wall_time_ms` + `query_count`; `db_time_ms` queda disponible, pero en SQLite suele valer `0.0`.

## Artefactos

- `benchmarks/baselines/default.json`
- `benchmark-results/latest.json`
- `docs/plans/2026-04-16-performance-benchmark-system-design.md`
