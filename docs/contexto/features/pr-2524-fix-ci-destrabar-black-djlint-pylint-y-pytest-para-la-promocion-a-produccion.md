# Contexto de feature PR #2524 - fix(ci): destrabar black, djlint, pylint y pytest para la promoción a producción

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/2524
- Base: `development`
- Rama origen: `fix/ci-checks-verdes-promocion-2522`
- Autor: `juanikitro`

## Contexto funcional

- CI / promoción a producción

## Arquitectura tocada

- Hay cambios en vistas web y puede existir impacto en permisos o renderizado.
- Se modifican templates, con posible impacto visual o de composición UI.

## Decisiones y supuestos detectados

- Tipo de cambio declarado: fix
- Área principal declarada: CI, tooling de lint, mapa de arquitectura
- Impacto usuario declarado: Ninguno (sin cambio de comportamiento observable)
- Riesgos / rollback: Bajo. Revert directo del commit; el único cambio no cosmético es el alcance del test de nonce y el disable de pylint.

## Design system y UI

- El PR toca piezas de UI y conviene revisar consistencia visual con el patrón existente.
- Archivos visuales relevantes: admisiones/templates/admisiones/admisiones_tecnicos_form.html, core/templates/core/mapa_arquitectura.html

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-2524.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `admisiones/templates/admisiones/admisiones_tecnicos_form.html`
- `core/management/commands/generar_mapa_arquitectura.py`
- `core/templates/core/mapa_arquitectura.html`
- `core/views.py`
- `docs/registro/cambios/2026-09-16-ci-verde-promocion-produccion.md`
- `scripts/arquitectura/generar_mapa.py`
- `scripts/ci/pr_lint_tools.py`
- `tests/test_docker_entrypoint_unit.py`
- `tests/test_mapa_arquitectura_generador.py`
- `tests/test_pr_lint_tools_unit.py`
- `tests/test_templates_inline_scripts_nonce_unit.py`
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
