# 2026-04-01 - Decisión de resolver el conflicto de migraciones con merge migration

## Decisión

Resolver el conflicto entre `0021_expandir_nomina_cdi` y `0022_alter_centrodeinfancia_ambito_and_more` con una migración de merge vacía.

## Motivo

- Preserva ambas ramas históricas.
- Evita modificar migraciones ya creadas.
- El cambio no requiere ordenar ni transformar datos.

## Alternativas evaluadas

- Reescribir `0021_expandir_nomina_cdi` para que dependa de `0022`.
- Reescribir `0022` para que dependa de `0021_expandir_nomina_cdi`.

Se descartaron porque implican tocar migraciones ya emitidas y no aportan valor frente a un merge explícito.
