# Fix migrate en `comedores` por rename de indices de auditoria

## Fecha
- 2026-04-04

## Problema
- `python manage.py migrate` fallaba en MySQL al aplicar `comedores.0033_rename_comedores_a_comedor_89ef7d_idx_comedores_a_comedor_4b1714_idx_and_more`.
- La migracion intentaba renombrar indices de `AuditColaboradorEspacio` asumiendo que siempre existian con el nombre historico (`comedores_a_comedor_89ef7d_idx` y equivalentes).
- En algunos estados reales de base, ese indice ya estaba con el nombre nuevo o no estaba presente, lo que hacia que MySQL devolviera `OperationalError (1176)`.

## Decision
- Se mantuvo el mismo estado logico de migraciones, pero la operacion de base se volvio idempotente.
- La migracion ahora inspecciona los indices existentes y:
  - renombra si encuentra el indice viejo,
  - no hace nada si ya existe el indice nuevo,
  - crea el indice nuevo si no existe ninguno de los dos.

## Impacto
- No cambia el esquema final esperado por Django.
- Evita que una base nueva o un estado intermedio de desarrollo queden bloqueados al migrar.
- Se agregaron tests unitarios del helper de migracion para cubrir rename, no-op y creacion.

## Validacion esperada
- `python manage.py migrate --noinput` debe completar sin el error `Key 'comedores_a_comedor_89ef7d_idx' doesn't exist`.
