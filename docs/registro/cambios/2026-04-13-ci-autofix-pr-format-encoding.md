# Cambio: autofix de formato y encoding en PRs

## Fecha

- 2026-04-13

## Alcance

- `.github/workflows/lint.yml`
- `scripts/ci/pr_lint_tools.py`

## Resumen

- Se agrego un job `autofix` al workflow de lint para PRs del mismo repositorio.
- El job corrige automaticamente:
  - formato Python con `black` sobre archivos `.py` cambiados en el PR
  - formato de templates con `djlint --reformat` sobre templates cambiados
  - secuencias tipicas de mojibake/encoding en archivos de texto modificados
- Si el bot aplico cambios, hace commit y push directo a la branch origen del PR.
- Despues del autofix, los jobs `encoding_check`, `black` y `djlint` vuelven a validar y fallan si aun queda algo no corregible automaticamente.

## Decision operativa

- El autofix solo corre en `pull_request` cuando la branch origen pertenece al mismo repositorio.
- En forks o eventos `push`, el workflow se mantiene en modo validacion sin intentar escribir.
- Se agrego `concurrency` para cancelar corridas viejas del mismo PR cuando el bot empuja un commit de autofix.

## Impacto esperado

- Menos fallas manuales por formato en PRs internos.
- Menos idas y vueltas de revision por errores triviales de `black`, `djlint` o mojibake comun.
- Si el problema no se puede corregir de forma segura, la CI sigue fallando para exigir intervencion humana.
