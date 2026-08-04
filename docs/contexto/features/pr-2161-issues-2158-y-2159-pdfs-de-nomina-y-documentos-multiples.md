# Contexto de feature PR #2161 - Issues 2158 y 2159: PDFs de nómina y documentos múltiples

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/2161
- Base: `development`
- Rama origen: `fixex-27-07`
- Autor: `PabloCao1`

## Contexto funcional

- No informado explícitamente; inferir desde el título del PR y el diff.

## Arquitectura tocada

- El PR toca lógica en `services/`, por lo que impacta reglas de negocio u orquestación.
- Hay cambios en capa API/DRF y conviene revisar contratos de request/response.
- Hay cambios en vistas web y puede existir impacto en permisos o renderizado.
- Se modifican templates, con posible impacto visual o de composición UI.
- Existen cambios de persistencia o migraciones que requieren revisión de datos.

## Decisiones y supuestos detectados

- Tipo de cambio declarado: No informado
- Área principal declarada: No informada
- Impacto usuario declarado: No informado
- Riesgos / rollback: No informado

## Design system y UI

- El PR toca piezas de UI y conviene revisar consistencia visual con el patrón existente.
- Archivos visuales relevantes: comedores/templates/comedor/nomina_asistencia_historial.html

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-2161.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `comedores/templates/comedor/nomina_asistencia_historial.html`
- `comedores/views/nomina.py`
- `docs/registro/cambios/2026-07-28-issues-2158-2159-pwa.md`
- `pwa/api_views.py`
- `pwa/services/nomina_destinatarios_pdf_service.py`
- `rendicioncuentasmensual/models.py`
- `tests/test_pwa_comedores_api.py`
- `tests/test_pwa_nomina_api.py`
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`
- `docs/registro/cambios/2026-07-28-issues-2158-2159-pwa.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
