# 2026-03-13 - CI para documentación automática de PRs y changelog

## Contexto

Se necesitaba reducir trabajo manual en la disciplina spec-as-source y acercar a SISOC a un flujo donde cada PR deje contexto persistente útil para agentes y revisores.

Además, `CHANGELOG.md` debía poder actualizarse automáticamente en el flujo de release a producción sin introducir una herramienta externa de versionado semántico.

## Cambios aplicados

- Se agregó el workflow `.github/workflows/pr-docs.yml` para eventos `pull_request` a `development` y `main`.
- Se implementó `scripts/ci/pr_doc_automation.py` para generar:
  - `docs/registro/prs/PR-<numero>.md`
  - `docs/contexto/features/pr-<numero>-<slug>.md`
  - `docs/registro/releases/pending/YYYY-MM-DD-pr-<numero>.md` solo para PRs a `main`
  - `CHANGELOG.md` regenerado para la release objetivo solo en PRs a `main`
- Se reforzó `.github/pull_request_template.md` con metadata estructurada para facilitar el parseo determinista del cuerpo del PR.
- Se documentaron las nuevas carpetas automáticas en `docs/indice.md`, `docs/agentes/guia.md` y `docs/registro/releases/`.
- Se agregaron tests unitarios enfocados en el generador.

## Impacto esperado

- Cada PR deja trazabilidad documental estable dentro del repo.
- Los agentes futuros pueden reconstruir contexto de feature sin depender solo del diff o de la memoria conversacional.
- El changelog del deploy a producción se puede preparar automáticamente desde el PR a `main`.

## Validación

- `pytest tests/test_pr_doc_automation_unit.py`

## Riesgos y rollback

- En PRs del mismo repositorio, el workflow hará commit automático a la rama origen; si la metadata del PR está incompleta, algunas secciones usarán fallbacks.
- El rollback consiste en remover `pr-docs.yml`, los scripts de generación y las carpetas/documentación asociadas.
