# CI: detectar artefactos spec-as-source no trackeados

## Cambio

El workflow `pr-docs.yml` ahora detecta archivos nuevos con `git status
--porcelain --untracked-files=all`, en lugar de basarse solo en `git diff`.

Para ramas internas no protegidas conserva el commit automático. Para ramas
protegidas y forks, si el generador deja artefactos pendientes, el check falla
y muestra los paths y el comando para regenerarlos.

## Motivo

`git diff --quiet` no informa archivos no trackeados. Por eso los PR a
`development` podían aprobar `sync_pr_artifacts` aunque faltaran
`docs/registro/prs/PR-<n>.md` y `docs/contexto/features/pr-<n>-*.md`.

## Riesgo y rollback

Los PR de forks o ramas protegidas que no incluyan artefactos pasarán a quedar
bloqueados hasta incorporarlos. El rollback es revertir el cambio del workflow;
no se amplían permisos ni se usa `pull_request_target`.
