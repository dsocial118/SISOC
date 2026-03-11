# 2026-03-12 - Pre-commit con black y pylint (sin djlint)

## Resumen

Se extendió la configuración de `pre-commit` para incluir:
- formateo automático de `black` (sin `--check`),
- chequeo de `pylint` con `.pylintrc`,
- manteniendo `gitleaks` existente.

No se agregó `djlint`, en línea con el alcance solicitado.

## Detalle técnico

- Archivo modificado: `.pre-commit-config.yaml`
- Hooks agregados:
  - `psf/black` `24.8.0` con `--config=pyproject.toml` (formatea en pre-commit)
  - hook local `pylint` ejecutando `pylint $(git ls-files "*.py") --rcfile=.pylintrc`

## Impacto

- Los pre-commits ahora ejecutan formateo de `black` y validación de `pylint` en Python.
- Se mantiene fuera de pre-commit la validación de templates (`djlint`).
