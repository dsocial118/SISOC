# 2026-07-21 - Módulos nuevos extraíbles dentro del monolito modular

## Estado

Aceptada.

## Contexto

SISOC es un monolito Django con apps de dominio, una sola configuración y una
base MySQL compartida. El código actual contiene dependencias históricas entre
apps, cache local y thread-local, por lo que mover una app existente a otro
repositorio no sería un corte mecánico.

La issue #1931 propone avanzar primero con boundaries y contratos de imports,
sin partir la base ni bloquear el desarrollo diario. El ratchet inicial de
`import-linter` ya protege `core`, `users` y `ciudadanos`, pero no define aún
cómo debe nacer un dominio nuevo.

## Decisión

Todo dominio nuevo se construirá como un **vertical extraíble** dentro del
monolito, salvo que se clasifique explícitamente como parte de un bounded
context existente o como cambio de kernel.

El vertical tendrá tablas y migraciones propias, un `api.py` público basado en
IDs/DTOs, y contratos `import-linter` que impidan imports a sus internos. Podrá
referenciar sólo un kernel declarado. No tendrá acoplamientos a otro vertical,
estado correcto en cache local/thread-local ni side effects cross-domain
ocultos.

No se crearán ahora repositorios, deployables, APIs internas, Redis, SSO ni una
base separada. Cuando haya motivo operativo para extraerlo, el nuevo proyecto
conservará las tablas propias y mapeará el kernel con `managed=False`.

La guía normativa es `docs/ia/MODULAR_BOUNDARIES.md`.

## Consecuencias

- Cada feature que cree una app o agregue una dependencia interdominio debe
  clasificarla antes de diseñarla.
- Los patrones legacy de apps existentes no habilitan nuevas excepciones en
  `.importlinter`.
- Las migraciones de esquema continuarán coordinándose mientras se comparta la
  misma base lógica; repos separados no equivalen todavía a microservicios con
  independencia de datos.
- Si una necesidad de UI global, RENAPER u otro recurso común no tiene una
  extensión pública, se abrirá primero una tarea de boundary en lugar de sumar
  un import directo.

## Alternativas consideradas

1. **Crear microservicios y repositorios ahora.** Descartado: agrega
   infraestructura y no resuelve las FKs ni el acoplamiento de datos actual.
2. **Mantener el monolito sin una regla para módulos nuevos.** Descartado:
   reproduce el grafo de dependencias que la Fase 0 busca frenar.
3. **Partir la base de datos antes de separar código.** Descartado por ahora:
   requiere resolver integridad referencial y transacciones distribuidas.

## Referencias

- Issue #1931: Modularización de SISOC.
- `docs/plans/2026-06-22-monolito-modular-fase-0.md`
- `docs/registro/decisiones/2026-06-23-import-linter-ratchet-fase-0.md`
