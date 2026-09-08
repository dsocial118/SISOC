# Orquestación de promoción automática y rollback trazable

## Contexto

La promoción semanal requería que Codex esperara checks y dejaba pasos manuales
para integrar ramas. Además, un runner de deploy podía obtener una revisión más
nueva que la aprobada por el Environment.

## Cambios aplicados

- Se agregó un orquestador por eventos y auto-merge nativo para PRs de
  preparación y el PR final `development -> main`.
- Se añadieron gates de evidencia para el pre-deploy, incluyendo causa raíz,
  regresión y revisión independiente cuando hay un fix funcional.
- La sincronización `main -> development/homologacion` arma auto-merge nativo;
  el push que realiza GitHub dispara el deploy del destino.
- El deploy exige el SHA del evento antes del downtime y registra evidencia de
  migraciones y health luego de actualizar el entorno.
- El changelog/spec-as-source puede generarse a partir del diff real de la
  promoción, incluso fuera de un evento `pull_request`.

## Impacto esperado

Los merges rutinarios se completan de manera automática después de los gates.
La única aprobación operativa esperada es la del Environment `production` para
el SHA vigente. Cada promoción deja un tag de rollback del `main` previo.

## Validación

- Tests unitarios focalizados de los helpers de documentación, deploy y
  orquestación.
- Validación sintáctica de Bash, JavaScript y workflows YAML.

## Riesgos y rollback

- La activación de auto-merge y checks obligatorios depende de un administrador
  de GitHub; hasta entonces el workflow aplica sus propios gates, pero la
  protección del repositorio no cambia.
- Si un tag estable ya existe con otro SHA, la promoción se bloquea. El rollback
  usa ese tag y el procedimiento documentado para datos/migraciones.
