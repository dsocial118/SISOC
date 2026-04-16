# 2026-03-13 - Automatizar documentación de PR y changelog en CI

## Estado

Aprobada

## Contexto

SISOC ya exige disciplina spec-as-source y registro en `docs/`, pero la generación de contexto seguía dependiendo en gran parte de acciones manuales del agente o del revisor.

Además, no existía automatización para:

- documentar cada PR en una ruta estable del repo
- consolidar contexto reutilizable para agentes futuros
- mantener `CHANGELOG.md` al día durante el flujo de release a producción

## Decision

Implementar una automatización propia del repo, disparada por `pull_request`, basada en scripts Python y GitHub Actions, con commit automático a la rama del PR.

La automatización:

- genera documentación por PR en `docs/registro/prs/`
- genera contexto de feature en `docs/contexto/features/`
- genera release notes preliminares solo para PRs a `main`
- regenera `CHANGELOG.md` solo para PRs a `main`

No se usarán LLMs en CI ni acciones externas para inferencia de contenido.

## Consecuencias

- El repo gana trazabilidad documental automática y consistente con spec-as-source.
- Se reduce dependencia de disciplina manual para construir contexto reutilizable.
- Se agrega lógica propia de generación documental que requerirá mantenimiento y tests.
- Los documentos canónicos de arquitectura/dominio no se tocarán automáticamente; el contexto incremental quedará acoplado al PR que lo originó.

## Referencias

- `docs/plans/2026-03-13-pr-docs-changelog-automation-design.md`
- `AGENTS.md`
- `docs/registro/README.md`
