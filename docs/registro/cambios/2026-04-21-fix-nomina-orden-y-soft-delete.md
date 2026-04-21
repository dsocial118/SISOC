# 2026-04-21 - Orden de nómina y exclusión de soft-delete

## Contexto
En `/comedores/<comedor_pk>/admision/<admision_pk>/nomina/` se detectó un caso donde
una persona activa no aparecía en la página 1 del listado, pero sí surgía al buscar
por DNI. El problema ocurría cuando la admisión tenía muchas filas recientes en
estado `baja`, porque la nómina se paginaba con el orden por defecto de `fecha`
descendente.

Además, el criterio funcional esperado para la pantalla es:
- mostrar primero las personas `activo`,
- dejar `espera` y `baja` al final,
- no reexponer registros con baja lógica (`soft-delete`) ni en listado ni en búsqueda.

## Cambios aplicados

### 1) Orden explícito de nómina por prioridad de estado
- Archivo: `comedores/services/comedor_service/impl.py`
- Se agregó `_order_nomina_queryset(...)`.
- La prioridad aplicada es:
  - `activo`
  - `espera`
  - `baja`
- Dentro de cada grupo se mantiene orden por `fecha` desc y `id` desc.

Resultado: la página 1 prioriza asistentes activos aunque existan muchas bajas más
recientes.

### 2) Reutilización del orden en ambos flujos web
- Archivo: `comedores/services/comedor_service/impl.py`
- El helper se aplica en `_build_nomina_page(...)`, por lo que cubre:
  - `get_nomina_detail(admision_pk, ...)`
  - `get_nomina_detail_by_comedor(comedor_pk, ...)`

Resultado: el comportamiento queda consistente entre nómina por admisión y nómina
directa de programas 3/4 sin alterar la lógica nueva que ya trae `development`
para deduplicar por ciudadano.

### 3) Regresión para búsqueda y baja lógica
- Archivo: `comedores/tests.py`
- Se agregó un test que cubre:
  - activos antiguos + muchas bajas recientes,
  - prioridad visual de activos en la página 1,
  - exclusión de un registro soft-deleted incluso cuando se busca su DNI.

## Validación
- `docker compose run --rm django pytest comedores/tests.py -k prioriza_activos_y_excluye_soft_deleted -q`
- `docker compose run --rm django pytest comedores/tests.py -k nomina -q`
- `docker compose run --rm django black --check comedores/tests.py comedores/services/comedor_service/impl.py --config pyproject.toml`

## Notas
- `pylint` sobre `comedores/services/comedor_service/impl.py` sigue reportando deuda
  previa del módulo (`too-many-lines`, imports legacy y falsos positivos de imports),
  sin observaciones nuevas específicas del helper agregado en este cambio.
