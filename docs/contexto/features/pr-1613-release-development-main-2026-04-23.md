# Contexto de feature PR #1613 - Release: development -> main (2026-04-23)

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/1613
- Base: `main`
- Rama origen: `development`
- Autor: `juanikitro`

## Contexto funcional

- Este PR es el corte exacto pedido para promocionar `development` sobre `main`.
- El objetivo del saneamiento asociado no es introducir funcionalidad nueva sino dejar `development` en condiciones reales de merge a produccion.
- El analisis de `2026-04-23` detecto dos bloqueos concretos previos al deploy:
  - regresion funcional en `admisiones` hacia `acompanamientos`;
  - workflow `pr-docs` incompatible con ramas protegidas.

## Arquitectura tocada

- Servicios de negocio: `admisiones` y `acompanamientos`.
- Tooling CI/CD: `.github/workflows/pr-docs.yml`.
- Automatizacion spec-as-source: `scripts/ci/pr_doc_automation.py`.
- Documentacion de release: `docs/registro/prs/`, `docs/registro/releases/pending/` y `CHANGELOG.md`.

## Decisiones y supuestos detectados

- Tipo de cambio principal para el saneamiento: `fix`.
- Area principal: `release`.
- Impacto usuario esperado: indirecto, porque evita fallas de deploy/validacion y recupera una derivacion funcional ya existente.
- Se asume que los riesgos de datos de `acompanamientos` y `ciudadanos` se evaluan con su runbook propio, separado del saneamiento minimo de CI.
- Se asume que la fecha visible del release train debe mantenerse en `2026-04-23`, alineada al PR exacto `development -> main`.

## Design system y UI

- El corte productivo incluye cambios visibles en `VAT`, `centrodeinfancia`, `acompanamientos` y `admisiones`.
- Para este saneamiento puntual no se toco UI nueva; solo se normalizo trazabilidad y automatizacion del release.

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-1613.md`.
- Revisar `docs/registro/cambios/2026-04-23-analisis-predeploy-main.md` para el analisis base del delta `development -> main`.
- Revisar `docs/registro/cambios/2026-04-23-predeploy-saneamiento-release-main.md` para el fix minimo agregado despues del analisis inicial.
- Si vuelven a fallar checks del release:
  - `pytest`: revisar `admisiones/services/admisiones_service/impl.py` y `tests/test_admisiones_service_helpers_unit.py`.
  - `pr-docs`: revisar `.github/workflows/pr-docs.yml` y `scripts/ci/pr_doc_automation.py`.

## Trazabilidad

- Documento cargado manualmente para no depender de pushes automaticos sobre `development`.
- Debe actualizarse si el diff `origin/main..origin/development` cambia materialmente antes del merge final.
