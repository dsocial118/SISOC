# Artefactos de PR desde ramas protegidas

## Contexto

El workflow `pr-docs.yml` no puede commitear artefactos en una rama protegida
origen (`development`, `homologacion` o `main`). Sin embargo, el job
`sync_pr_artifacts` exigía esos archivos y bloqueaba las promociones aunque la
ausencia no afectara al código ni a la calidad de la entrega.

## Decisión

Para un PR interno cuya rama origen sea protegida, `sync_pr_artifacts` seguirá
identificando y mostrando los artefactos faltantes en el resumen de GitHub
Actions, pero finalizará exitosamente. Para ramas de trabajo o forks, conserva
el fallo estricto: allí la automatización debe poder generar y commitear los
artefactos o el PR debe traerlos.

## Alternativas descartadas

- Omitir el job para promociones: elimina la trazabilidad de artefactos
  faltantes.
- Volver advertencia todos los PR: ocultaría fallas reales en ramas de trabajo.

## Validación

- Validar la sintaxis y el diff del workflow.
- Comprobar estáticamente que el caso protegido devuelve éxito y que los demás
  casos mantienen `exit 1`.
- La ejecución remota de un PR de prueba es la prueba final del comportamiento.
