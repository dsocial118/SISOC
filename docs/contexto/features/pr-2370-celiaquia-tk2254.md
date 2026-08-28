# Contexto de feature PR #2370 - Celiaquia tk2254

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/2370
- Base: `development`
- Rama origen: `Celiaquia_Tk2254`
- Autor: `MariaNavarro90`

## Contexto funcional

- Celiaquía — control de acceso a los módulos Dashboard de Cupos y Reporte por provincias. Afecta a usuarios provinciales y de Nación (coordinadores y técnicos).

## Arquitectura tocada

- Se modifican templates, con posible impacto visual o de composición UI.
- Existen cambios de persistencia o migraciones que requieren revisión de datos.

## Decisiones y supuestos detectados

- Tipo de cambio declarado: Corrección de control de acceso + mejora de granularidad de permisos. Incluye migración de esquema y data migration.
- Área principal declarada: celiaquia (modelo, urls, global_urls, migraciones). Toca además templates/includes/sidebar/opciones.html, compartido por todos los módulos.
- Impacto usuario declarado: Los grupos estrictamente provinciales dejan de ver el Dashboard de Cupos; el resto conserva el acceso que tenía. Se corrige una exposición de datos nacionales a usuarios provinciales. A partir de ahora ambos permisos se asignan por separado desde el admin de grupos.
- Riesgos / rollback: La migración modifica permisos de grupos, por lo que el alcance se verificó en producción antes de promover (ver tabla): solo cambia el grupo provincial. Si un grupo legítimo de Nación quedara sin Dashboard, se resuelve asignando view_cupo_dashboard desde el admin, sin revertir nada. Rollback completo: python manage.py migrate celiaquia 0004.

## Design system y UI

- El PR toca piezas de UI y conviene revisar consistencia visual con el patrón existente.
- Archivos visuales relevantes: templates/includes/sidebar/opciones.html

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-2370.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `celiaquia/global_urls.py`
- `celiaquia/migrations/0005_alter_expediente_options.py`
- `celiaquia/migrations/0006_seed_permisos_dashboard_reporte.py`
- `celiaquia/models.py`
- `celiaquia/tests/test_permisos_dashboard_reporte.py`
- `celiaquia/tests/test_reporter_provincias.py`
- `celiaquia/urls.py`
- `docs/registro/cambios/2026-08-27-issue-2254-permisos-dashboard-reporte-celiaquia.md`
- `templates/includes/sidebar/opciones.html`
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`
- `docs/registro/cambios/2026-08-27-issue-2254-permisos-dashboard-reporte-celiaquia.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
