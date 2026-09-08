# Contexto de feature PR #2273 - Comedores #2142

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/2273
- Base: `development`
- Rama origen: `Comedores-#2142`
- Autor: `nehuen871`

## Contexto funcional

- No informado explícitamente; inferir desde el título del PR y el diff.

## Arquitectura tocada

- El PR toca lógica en `services/`, por lo que impacta reglas de negocio u orquestación.
- Se modifican templates, con posible impacto visual o de composición UI.
- Existen cambios de persistencia o migraciones que requieren revisión de datos.

## Decisiones y supuestos detectados

- Tipo de cambio declarado: No informado
- Área principal declarada: No informada
- Impacto usuario declarado: No informado
- Riesgos / rollback: No informado

## Design system y UI

- El PR toca piezas de UI y conviene revisar consistencia visual con el patrón existente.
- Archivos visuales relevantes: comedores/templates/comedor/nomina_form.html

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-2273.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `ciudadanos/migrations/0031_ciudadano_en_situacion_de_calle_and_more.py`
- `ciudadanos/models.py`
- `comedores/forms/comedor_form.py`
- `comedores/services/comedor_service/impl.py`
- `comedores/templates/comedor/nomina_form.html`
- `comedores/views/nomina.py`
- `docs/contexto/features/pr-2273-comedores-2142.md`
- `docs/registro/cambios/2026-08-10-alta-ciudadano-sin-dni-nomina.md`
- `docs/registro/prs/PR-2273.md`
- `tests/test_comedor_service_renaper_helpers_unit.py`
- `tests/test_comedor_sin_dni_form_unit.py`
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`
- `docs/contexto/features/pr-2273-comedores-2142.md`
- `docs/registro/cambios/2026-08-10-alta-ciudadano-sin-dni-nomina.md`
- `docs/registro/prs/PR-2273.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
