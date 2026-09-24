# Contexto de feature PR #2566 - VPSL: Cambios por Feedback

## Resumen

- PR: https://github.com/secretarianaf/SISOC/pull/2566
- Base: `development`
- Rama origen: `task/Cambios-VPSL-Itinerarios-Sedes-Jornadas`
- Autor: `Esteban-Royo`

## Contexto funcional

- Planificación, ejecución y registro de jornadas de Ver Para Ser Libres.

## Arquitectura tocada

- El PR toca lógica en `services/`, por lo que impacta reglas de negocio u orquestación.
- Hay cambios en vistas web y puede existir impacto en permisos o renderizado.
- Se modifican templates, con posible impacto visual o de composición UI.
- Existen cambios de persistencia o migraciones que requieren revisión de datos.

## Decisiones y supuestos detectados

- Tipo de cambio declarado: Mejora funcional, modelo de datos, seguridad y UX.
- Área principal declarada: Ver Para Ser Libres — itinerarios, jornadas y registros nominales.
- Impacto usuario declarado: Simplifica la planificación y mejora la precisión de sedes, diagnósticos y exportaciones.
- Riesgos / rollback: La migración 0015 debe aplicarse completa; el rollback puede reducir vehículos múltiples a una única opción histórica.

## Design system y UI

- El PR toca piezas de UI y conviene revisar consistencia visual con el patrón existente.
- Archivos visuales relevantes: static/custom/css/ver_para_ser_libre.css, ver_para_ser_libre/templates/ver_para_ser_libre/checklist_form.html, ver_para_ser_libre/templates/ver_para_ser_libre/itinerario_detail.html, ver_para_ser_libre/templates/ver_para_ser_libre/itinerario_form.html, ver_para_ser_libre/templates/ver_para_ser_libre/jornada_detail.html, ver_para_ser_libre/templates/ver_para_ser_libre/jornada_form.html, ver_para_ser_libre/templates/ver_para_ser_libre/registro_form.html

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-2566.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `AGENT_REPO_MAP.md`
- `docs/registro/cambios/2026-09-21-vpsl-ubicacion-jornadas.md`
- `docs/registro/cambios/2026-09-23-vpsl-catalogo-vehiculos.md`
- `docs/registro/cambios/2026-09-23-vpsl-graduacion-registros.md`
- `static/custom/css/ver_para_ser_libre.css`
- `ver_para_ser_libre/admin.py`
- `ver_para_ser_libre/forms.py`
- `ver_para_ser_libre/migrations/0015_vpsl_ubicacion_vehiculos_graduaciones.py`
- `ver_para_ser_libre/models.py`
- `ver_para_ser_libre/services/map_location.py`
- `ver_para_ser_libre/services/workflow.py`
- `ver_para_ser_libre/templates/ver_para_ser_libre/checklist_form.html`
- `ver_para_ser_libre/templates/ver_para_ser_libre/itinerario_detail.html`
- `ver_para_ser_libre/templates/ver_para_ser_libre/itinerario_form.html`
- `ver_para_ser_libre/templates/ver_para_ser_libre/jornada_detail.html`
- `ver_para_ser_libre/templates/ver_para_ser_libre/jornada_form.html`
- `ver_para_ser_libre/templates/ver_para_ser_libre/registro_form.html`
- `ver_para_ser_libre/tests/test_jornada_location.py`
- `ver_para_ser_libre/tests/test_workflow.py`
- `ver_para_ser_libre/urls.py`
- ... y 1 archivo(s) adicional(es) relacionados.
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
