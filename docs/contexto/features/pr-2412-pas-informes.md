# Contexto de feature PR #2412 - PAS:Informes

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/2412
- Base: `development`
- Rama origen: `task/Informes-PAS`
- Autor: `Esteban-Royo`

## Contexto funcional

- Consulta y exportación de información del padrón PAS y de su historial de cambios.

## Arquitectura tocada

- El PR toca lógica en `services/`, por lo que impacta reglas de negocio u orquestación.
- Hay cambios en vistas web y puede existir impacto en permisos o renderizado.
- Se modifican templates, con posible impacto visual o de composición UI.
- Existen cambios de persistencia o migraciones que requieren revisión de datos.

## Decisiones y supuestos detectados

- Tipo de cambio declarado: Nueva funcionalidad, modelo de persistencia, migración, servicio de negocio, endpoints y pantallas.
- Área principal declarada: PAS — Informes.
- Impacto usuario declarado: Los operadores autorizados pueden generar informes reproducibles del padrón PAS y descargar posteriormente la misma fotografía de resultados.
- Riesgos / rollback: La migración agrega la tabla y relaciones de PasInforme. El rollback elimina los informes persistidos, por lo que deben exportarse o respaldarse antes de revertir. El PR depende de la migración 0002 del PR anterior.

## Design system y UI

- El PR toca piezas de UI y conviene revisar consistencia visual con el patrón existente.
- Archivos visuales relevantes: pas/templates/pas/informe_detail.html, pas/templates/pas/informe_form.html, pas/templates/pas/informe_list.html, static/custom/js/pas_informe.js

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-2412.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `AGENT_REPO_MAP.md`
- `core/services/csv_export.py`
- `docs/registro/cambios/2026-09-01-informes-pas.md`
- `pas/admin.py`
- `pas/forms.py`
- `pas/migrations/0003_pasinforme.py`
- `pas/models.py`
- `pas/services/informe_service.py`
- `pas/templates/pas/informe_detail.html`
- `pas/templates/pas/informe_form.html`
- `pas/templates/pas/informe_list.html`
- `pas/tests/test_informe_service.py`
- `pas/urls.py`
- `pas/views.py`
- `static/custom/js/pas_informe.js`
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`
- `docs/registro/cambios/2026-09-01-informes-pas.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
