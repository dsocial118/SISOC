# Predeploy development -> main 2026-04-24

## Contexto

Se preparo un nuevo predeploy entre `origin/development` y `origin/main` con
worktree aislada y PR final obligatorio `development -> main`.

## Saneamiento aplicado

- `pr-docs.yml` deja de intentar push directo cuando el head del PR es una
  rama protegida (`development` o `main`) y reporta el diff generado en el
  summary del job.
- `scripts/ci/pr_doc_automation.py` respeta una fecha de release explicita en
  el body del PR antes de usar el fallback historico del proximo miercoles.
- `CHANGELOG.md` queda fechado para el PR final del 2026-04-24.
- Se corrigieron tres finales de archivo marcados por `git diff --check`.
- Ciudadanos respeta el cierre explicito de `requiere_revision_manual` cuando
  el campo se guarda de forma intencional. Esto permite que Comedores acepte en
  nomina a personas con DNI no validado por RENAPER cuya revision manual ya fue
  cerrada.
- `IntervencionCreateView` mueve validacion y asignacion de campos a helpers
  chicos para que el lint completo no bloquee el release por complejidad
  ciclomatica en la vista.

## Riesgo mitigado

El PR final a `main` usa `development` como rama origen. Si el workflow intentaba
commitear artefactos desde esa rama protegida, GitHub podia rechazar el push con
reglas de proteccion de rama y bloquear el release por automatizacion, no por
codigo funcional.

## Validacion esperada

- `git diff --check`
- Tests unitarios de `scripts/ci/pr_doc_automation.py`
- Regresiones de identidad/nomina de Comedores y modelo de Ciudadanos
- `pylint` sobre `intervenciones/views.py`
- Checks de GitHub Actions del PR de saneamiento y del PR final a `main`
