# Bootstrap de la sincronización descendente

## Contexto

La promoción semanal quedó detenida porque `main` todavía no era ancestro de
`development`. El workflow de sincronización se ejecutaba desde la rama por
defecto `development`, pero hacía checkout explícito de `main` antes de cargar
`.github/scripts/sync_main_downstream.js`.

El helper existe en `development` y no en el SHA vigente de `main`, por lo que
el job fallaba de forma determinista con `MODULE_NOT_FOUND` antes de crear el
PR técnico de sincronización.

## Cambio

El checkout de la automatización pasa a `development`, igual que el
orquestador de release. Así el workflow y el helper se cargan desde la misma
fuente versionada que GitHub Actions evalúa como rama por defecto.

Se agrega una regresión Node que valida ese contrato de bootstrap en el
workflow YAML. `deploy_guard`, que es el check requerido por la ruleset,
ejecuta esa prueba junto con la del orquestador de release.

## Compatibilidad y seguridad

El cambio no escribe en `main`, no relaja rulesets ni usa PATs. La GitHub App
sigue creando únicamente PRs técnicos `automation/sync-main-to-<destino>` y
GitHub conserva el auto-merge sujeto a los checks obligatorios.

Si la política futura exige ejecutar el helper desde `main`, ese archivo debe
promoverse primero a `main` mediante un flujo compatible; no debe volver a
apuntarse el checkout a una rama que no lo contiene.

## Validación y rollback

La prueba focalizada cubre el contrato workflow-helper y conserva las pruebas
de creación de PR técnico y auto-merge; el check requerido `deploy_guard` las
ejecuta en cada PR. El rollback consiste en restaurar el checkout a `main` solo
después de confirmar que el helper está presente en el SHA de `main` que
ejecutará el workflow.
