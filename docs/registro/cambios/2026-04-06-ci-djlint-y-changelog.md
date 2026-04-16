# 2026-04-06 - Ajuste de CI para templates y changelog

## Resumen

- El workflow de lint ahora ejecuta `djlint` solo sobre templates modificados en el diff, para fallar antes cuando el cambio toca HTML.
- La automatización de PR dejó de escribir `CHANGELOG.md` de forma automática.

## Motivo

- `djlint` estaba recorriendo demasiados archivos en cada ejecución.
- La generación automática del changelog estaba produciendo contenido incorrecto y no debía seguir sobrescribiendo el archivo principal.

## Alcance

- Se mantiene la generación de artefactos spec-as-source del PR.
- Se conserva la nota de release pendiente en `docs/registro/releases/pending/`.
- Ya no se actualiza `CHANGELOG.md` desde `scripts/ci/pr_doc_automation.py`.

