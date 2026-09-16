# Contexto de feature PR #2511 - Task/vpsl creacion multiprov

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/2511
- Base: `development`
- Rama origen: `task/VPSL-Creacion-multiprov`
- Autor: `Esteban-Royo`

## Contexto funcional

- Planificación de itinerarios, gestión de sedes y ubicación de jornadas VPSL.

## Arquitectura tocada

- El PR toca lógica en `services/`, por lo que impacta reglas de negocio u orquestación.
- Hay cambios en vistas web y puede existir impacto en permisos o renderizado.
- Se modifican templates, con posible impacto visual o de composición UI.
- Existen cambios de persistencia o migraciones que requieren revisión de datos.

## Decisiones y supuestos detectados

- Tipo de cambio declarado: Funcionalidad y correcciones.
- Área principal declarada: ver_para_ser_libre.
- Impacto usuario declarado: Más opciones de planificación; alta y edición de sedes más simples, con filtros provinciales consistentes.
- Riesgos / rollback: Revertir 0014 puede requerir completar datos opcionales y CUE faltantes; respaldar las sedes antes de revertir.

## Design system y UI

- El PR toca piezas de UI y conviene revisar consistencia visual con el patrón existente.
- Archivos visuales relevantes: ver_para_ser_libre/templates/ver_para_ser_libre/itinerario_form.html, ver_para_ser_libre/templates/ver_para_ser_libre/itinerario_list.html, ver_para_ser_libre/templates/ver_para_ser_libre/sede_form.html, ver_para_ser_libre/templates/ver_para_ser_libre/sede_list.html

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-2511.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `AGENT_REPO_MAP.md`
- `docs/registro/cambios/2026-09-15-vpsl-alta-sedes-simplificada.md`
- `docs/registro/cambios/2026-09-15-vpsl-creacion-itinerarios-cualquier-provincia.md`
- `docs/registro/cambios/2026-09-15-vpsl-jurisdicciones-equivalentes-caba.md`
- `ver_para_ser_libre/forms.py`
- `ver_para_ser_libre/migrations/0013_itinerariovpsl_create_any_province_permission.py`
- `ver_para_ser_libre/migrations/0014_sedevpsl_optional_school_data.py`
- `ver_para_ser_libre/models.py`
- `ver_para_ser_libre/services/sedes.py`
- `ver_para_ser_libre/templates/ver_para_ser_libre/itinerario_form.html`
- `ver_para_ser_libre/templates/ver_para_ser_libre/itinerario_list.html`
- `ver_para_ser_libre/templates/ver_para_ser_libre/sede_form.html`
- `ver_para_ser_libre/templates/ver_para_ser_libre/sede_list.html`
- `ver_para_ser_libre/tests/test_workflow.py`
- `ver_para_ser_libre/urls.py`
- `ver_para_ser_libre/views.py`
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
