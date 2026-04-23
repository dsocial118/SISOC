# Extracción temporal de PRs 1446, 1537 y 1606 fuera de development

## Contexto

Se retiran temporalmente de `development` tres implementaciones que ya habían sido mergeadas:

- `#1446`: nueva lógica de asociación entre Acompañamiento y Admisión.
- `#1537`: incorporación en nóminas y Legajo Ciudadano de personas sin DNI o con DNI no validado.
- `#1606`: posibilidad de eliminar documentación validada antes del Informe Técnico.

La extracción se hace sobre `origin/development` verificado el `2026-04-23` en `04bf76755`.

## Alcance de la extracción

La reversión es funcional, no estructural:

- se retiran rutas, vistas, templates visibles, filtros, badges, acciones y hooks de negocio asociados a estas implementaciones;
- se preserva la compatibilidad del grafo de migraciones ya encadenado en `development`;
- se mantienen en código los artefactos mínimos de modelo/schema que hoy exigen las migraciones;
- no se eliminan migraciones históricas ni se intenta volver atrás la base.

## Qué vuelve a development

`development` vuelve al comportamiento previo en estas superficies:

- `/ciudadanos/crear/` deja de permitir altas manuales sin validación RENAPER;
- `/ciudadanos/revision/` deja de estar disponible;
- `/acompanamientos/acompanamiento/...` deja de exponerse como superficie web activa;
- la admisión deja de permitir la eliminación documental técnica agregada por `#1606`;
- se quitan badges, filtros y wiring de identidad manual en nómina y legajo.

## Qué se conserva en development

Se conserva expresamente el commit `7e36063f3` (`restore territorial edit validation contract`), porque corresponde al contrato vigente de validación de `territorial_editar` y no forma parte de la extracción temporal.

También se conserva la compatibilidad de migraciones introducida alrededor de:

- `acompanamientos/0004` a `0008`
- `ciudadanos/0023` a `0028`
- `admisiones/0058`

## Branch estacionada

La funcionalidad retirada se reagrupa en una sola branch estacionada:

- `codex/park-development-1446-1537-1606`

Esa branch debe rearmar commits nuevos, mergeables a futuro, reintroduciendo:

- la superficie funcional de `#1446`;
- la superficie funcional de `#1537`;
- los commits funcionales de `#1606`, excluyendo nuevamente `7e36063f3`.

## Trade-offs

- Se prioriza preservar `migrate` y la compatibilidad entre entornos por encima de un rollback total del schema.
- Quedan artefactos de compatibilidad dormidos en `development`, pero sin exposición funcional al usuario final.
