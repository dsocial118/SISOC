# Contexto de feature PR #2555 - Bug en guardado de localidad #2491 y este issue FIX: Datos de nómina Comedores #2507

## Resumen

- PR: https://github.com/secretarianaf/SISOC/pull/2555
- Base: `development`
- Rama origen: `Bug-en-guardado-de-Localidad-#2491`
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
- Archivos visuales relevantes: comedores/templates/comedor/comedor_detail.html, comedores/templates/comedor/responsable_tarjeta_form.html, static/custom/css/comedor_detail.css, static/custom/css/nuevo_comedor.css

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-2555.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `comedores/forms/comedor_form.py`
- `comedores/migrations/0061_comedor_responsable_tarjeta_municipio.py`
- `comedores/models.py`
- `comedores/services/comedor_service/impl.py`
- `comedores/templates/comedor/comedor_detail.html`
- `comedores/templates/comedor/responsable_tarjeta_form.html`
- `comedores/tests/test_responsable_tarjeta_form.py`
- `comedores/views/comedor.py`
- `docs/contexto/features/pr-2555-bug-en-guardado-de-localidad-2491-y-este-issue-fix-datos-de-nomina-comedores-2507.md`
- `docs/registro/cambios/2026-09-22-responsable-tarjeta-municipio.md`
- `docs/registro/prs/PR-2555.md`
- `static/custom/css/comedor_detail.css`
- `static/custom/css/nuevo_comedor.css`
- `tests/test_comedor_service_characterization_db.py`
- `tests/test_comedor_service_renaper_helpers_unit.py`
- `tests/test_comedores_nomina_resumen_activos_db.py`
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
