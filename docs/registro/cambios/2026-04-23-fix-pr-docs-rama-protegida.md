# 2026-04-23 - `pr-docs` no debe pushear directo a ramas protegidas

## Contexto

- El workflow `.github/workflows/pr-docs.yml` genera documentación automática por PR y, cuando detecta cambios, intenta commitearlos sobre la rama origen.
- En el PR de release `development -> main` (`#1613`), la rama origen es `development`, que está protegida por reglas de repositorio y rechaza pushes directos con `GH013`.

## Cambio aplicado

- Se agregó una detección explícita de ramas origen protegidas (`development` y `main`).
- Para esas ramas, el workflow sigue generando artefactos y reporta el diff en el summary del job, pero deja de intentar `git push`.
- El commit automático se conserva para ramas de feature no protegidas dentro del mismo repositorio.

## Impacto

- Los PRs exactos `development -> main` dejan de fallar por intentar violar la regla "Changes must be made through a pull request".
- La documentación automática sigue siendo visible y auditable desde el summary del workflow.
- Si esos artefactos deben persistirse en una rama protegida, tienen que entrar mediante un PR explícito hacia esa rama.

## Validación

- Reproducción del fallo original con `GH013` en `#1613`.
- Generación local de los artefactos esperados para `#1613` y verificación de que el único problema del job era el `git push` a `development`.
