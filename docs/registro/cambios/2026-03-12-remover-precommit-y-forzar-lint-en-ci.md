# 2026-03-12 - Remover pre-commit y forzar lint en CI

## Resumen

Se eliminó la configuración local de `pre-commit` del repositorio para que la validación no dependa de instalación en cada entorno de desarrollo.

Se reforzó CI para que el workflow de lint se ejecute tanto en `pull_request` como en `push` a `main` y `development`.

## Detalle técnico

- Archivo eliminado: `.pre-commit-config.yaml`
- Archivo modificado: `.github/workflows/lint.yml`
  - Se agregó trigger `push` para ramas `main` y `development`.
  - Se mantienen jobs de `black`, `djlint` y `pylint`.

## Impacto

- Los checks de lint quedan asegurados por CI aunque un desarrollador no tenga `pre-commit` instalado.
- La validación local pasa a ser opcional/manual.
