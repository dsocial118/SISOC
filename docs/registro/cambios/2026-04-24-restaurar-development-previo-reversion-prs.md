# Restaurar development previo a la reversion de PRs

Fecha: 2026-04-24

## Contexto

El 2026-04-23 se mergearon en `development` los PRs #1619 y #1621 desde
`codex/revert-development-1446-1537-1606`. Esos cambios intentaban extraer
temporalmente los PRs #1446, #1537 y #1606, pero el resultado no dejo la rama
en un estado valido para continuar el trabajo.

El ultimo punto bueno identificado antes de esa extraccion fue `04bf76755`,
merge del PR #1612 (`task/predeploy-development-main-20260423`).

## Decision

Restaurar `development` mediante commits de revert sobre los merges #1621 y
#1619, sin `reset`, sin force-push y sin reescribir historia de la rama
protegida.

## Resultado esperado

La rama de restauracion debe dejar el arbol equivalente a `04bf76755`, salvo
por este registro documental. Con esto se recupera el comportamiento que ya
estaba integrado desde los PRs #1446, #1537 y #1606.
