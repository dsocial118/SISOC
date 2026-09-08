# Sincronización descendente compatible con checks estrictos

## Contexto

El PR automático `main -> development` quedaba bloqueado cuando la rama destino
avanzaba: la ruleset exige que el head esté actualizado y los checks de PR se
ejecutaban sobre `main`, sin el contexto actual de `development`.

## Cambio

El workflow ahora crea o actualiza una rama técnica por destino,
`automation/sync-main-to-<destino>`, partiendo de la rama destino e incorporando
`main` mediante merges no forzados. El PR hacia `development` u `homologacion`
sale de esa rama y conserva el auto-merge nativo.

## Impacto y límites

Los checks requeridos se ejecutan sobre un head actualizado, sin promover los
extras del destino hacia `main`. Un conflicto al incorporar cualquiera de las
ramas mantiene el PR abierto y falla la sincronización; no hay resolución ni
force-push automáticos. Los PRs directos históricos se cierran solo si fueron
creados por `github-actions[bot]` y coinciden con el título esperado, para no
dejar dos auto-merges hacia el mismo destino.
