# 2026-03-25 - Fix del job `sync_pr_artifacts` en GitHub Actions

## Contexto

El workflow `.github/workflows/pr-docs.yml` ejecuta `scripts/ci/pr_doc_automation.py`
en cada evento `pull_request` para regenerar artefactos spec-as-source del PR.

El job `sync_pr_artifacts` estaba fallando al consultar la API de GitHub para obtener
los archivos modificados, con error `HTTP Error 404: Not Found`.

## Causa raíz

`fetch_changed_files()` construía la URL del endpoint de GitHub codificando el valor
completo de `repo_full_name` con `urllib.parse.quote(..., safe="")`.

Eso transformaba `owner/repo` en `owner%2Frepo`, produciendo una URL inválida para el
endpoint esperado por GitHub:

- incorrecto: `/repos/owner%2Frepo/pulls/<numero>/files`
- correcto: `/repos/owner/repo/pulls/<numero>/files`

## Cambio aplicado

- Se corrigió la construcción del path para preservar la barra entre owner y repo.
- Se agregó un test de regresión que verifica la URL usada por
  `fetch_changed_files()`.

## Impacto

- El job vuelve a poder consultar los archivos modificados del PR.
- No cambia el formato de los artefactos generados; solo corrige la llamada a la API.

## Validación esperada

- `pytest tests/test_pr_doc_automation_unit.py`
