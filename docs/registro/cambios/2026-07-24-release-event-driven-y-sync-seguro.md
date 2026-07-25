# 2026-07-24 - Release event-driven y sincronización descendente segura

## Cambios

- Se eliminaron los cron horarios de `release-orchestrator.yml` y
  `sync-main-downstream.yml`.
- La promoción continúa mediante el dispatch de la tarea de pre-deploy, el
  cierre del PR temporal y la finalización de sus checks; la sincronización
  descendente se inicia con cada push a `main`.
- `workflow_dispatch` queda disponible como recuperación explícita, sin una
  sesión de Codex esperando CI ni reconciliaciones periódicas.
- Se documentó la separación de rulesets: `main` conserva los cuatro checks
  compartidos, `release_baseline`, rama al día y cero aprobaciones; las ramas
  descendentes mantienen los cuatro checks y cero aprobaciones, pero no
  exigen una actualización imposible de `main` con cambios exclusivos de QA o
  HML.

## Motivo

Una ruleset estricta compartida por `main`, `development` y `homologacion`
bloqueaba un PR `main -> development`: para integrarlo exigía que `main`
incluyera antes los commits exclusivos de `development`, invirtiendo el sentido
de la sincronización y arriesgando una promoción no revisada.

## Riesgos y rollback

- Si un evento de GitHub no llega a ejecutar el workflow, se puede despachar
  manualmente el workflow correspondiente; no hay un cron que lo recupere por
  sí solo.
- La protección de `main` no se relaja: conserva rama al día, los checks de CI
  y el baseline de rollback antes del auto-merge.
- La recuperación de un PR descendente con conflicto sigue siendo manual y por
  PR; no se usan rebase ni force-push automáticos.
