# Contexto de feature PR #2401 - fix(cdi): normalizar departamento de contacto

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/2401
- Base: `development`
- Rama origen: `codex/fix-cdi-geografia-selects`
- Autor: `juanikitro`

## Contexto funcional

- No informado explícitamente; inferir desde el título del PR y el diff.

## Arquitectura tocada

- No se detectó un patrón arquitectónico dominante más allá del diff observado.

## Decisiones y supuestos detectados

- Tipo de cambio declarado: No informado
- Área principal declarada: No informada
- Impacto usuario declarado: No informado
- Riesgos / rollback: No informado

## Design system y UI

- El PR toca piezas de UI y conviene revisar consistencia visual con el patrón existente.
- Archivos visuales relevantes: static/custom/js/trabajadorForm.js

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-2401.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `centrodeinfancia/forms.py`
- `centrodeinfancia/tests/test_trabajador_form.py`
- `docs/registro/cambios/2026-08-31-correccion-geografia-trabajador-cdi.md`
- `static/custom/js/trabajadorForm.js`
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`
- `docs/registro/cambios/2026-08-31-correccion-geografia-trabajador-cdi.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
