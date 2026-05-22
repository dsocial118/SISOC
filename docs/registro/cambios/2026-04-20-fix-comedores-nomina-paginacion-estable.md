# Fix comedores: paginacion estable en nomina

**Fecha:** 2026-04-20

## Que se ajusto

- Se fijo un orden total para la paginacion de nomina en comedores: primero `fecha` descendente y luego `id` descendente.
- El cambio se aplico en el helper comun de paginacion, por lo que cubre tanto la nomina por admision como la nomina directa por comedor.
- Se agrego un test de regresion que fuerza multiples filas con la misma `fecha` y verifica que la pagina 1 y la pagina 2 se construyan con un desempate estable por `id`.

## Decision clave

La deduplicacion visible por ciudadano no alcanza si la paginacion queda apoyada en un orden parcial. Para evitar que una misma fila pueda saltar entre paginas ante empates de `fecha`, la vista debe paginar con un orden deterministico y total.

## Validacion esperada

- Cuando muchas filas comparten la misma `fecha`, la pagina 1 debe mostrar primero los registros mas nuevos.
- La pagina 2 no debe reutilizar filas de la pagina 1 por cambios de orden entre requests.
