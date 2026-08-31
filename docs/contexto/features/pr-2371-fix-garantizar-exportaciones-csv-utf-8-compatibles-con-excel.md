# Contexto de feature PR #2371 - fix: garantizar exportaciones CSV UTF-8 compatibles con Excel

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/2371
- Base: `development`
- Rama origen: `codex/fix-utf8-exports`
- Autor: `juanikitro`

## Contexto funcional

- exportaciones descargables de SISOC abiertas con Microsoft Excel.

## Arquitectura tocada

- El PR toca lógica en `services/`, por lo que impacta reglas de negocio u orquestación.
- Hay cambios en vistas web y puede existir impacto en permisos o renderizado.

## Decisiones y supuestos detectados

- Tipo de cambio declarado: bugfix transversal de codificación.
- Área principal declarada: core / exportaciones CSV.
- Impacto usuario declarado: tildes, ñ y demás Unicode se conservan al abrir CSV directamente en Excel.
- Riesgos / rollback: revertir el commit; no hay migraciones ni cambios de datos.

## Design system y UI

- Sin cambios visibles de UI o design system detectados en el diff.

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-2371.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `AGENT_REPO_MAP.md`
- `VAT/services/reportes_inscripciones_asistencia.py`
- `VAT/test_tipo_alumno.py`
- `audittrail/views.py`
- `celiaquia/services/cruce_service/impl.py`
- `centrodefamilia/tests/test_beneficiarios_export.py`
- `centrodefamilia/views/beneficiarios_export.py`
- `core/admin_import_export.py`
- `core/mixins.py`
- `core/services/csv_export.py`
- `docs/implementaciones/exportar_listados.md`
- `docs/plans/2026-08-28-exportaciones-utf8-excel-design.md`
- `docs/registro/cambios/2026-08-28-exportaciones-utf8-excel.md`
- `tests/test_admin_import_export.py`
- `tests/test_audittrail_views_unit.py`
- `tests/test_cruce_service_helpers_unit.py`
- `tests/test_csv_export.py`
- `tests/test_csv_export_architecture.py`
- `users/views_user_import.py`
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`
- `docs/implementaciones/exportar_listados.md`
- `docs/plans/2026-08-28-exportaciones-utf8-excel-design.md`
- `docs/registro/cambios/2026-08-28-exportaciones-utf8-excel.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
