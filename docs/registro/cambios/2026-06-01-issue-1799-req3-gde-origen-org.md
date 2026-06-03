# 2026-06-01 — Issue #1799 (Req 3): el Numero de GDE se gestiona desde el Legajo de la Organizacion

Rama: `claude/issue-1799-req3-gde-origen-org` (apilada sobre Req 2)
Plan: [docs/plans/2026-06-01-issue-1799-documentacion-organizacion-admisiones.md](../../plans/2026-06-01-issue-1799-documentacion-organizacion-admisiones.md)
Decision: [docs/registro/decisiones/2026-06-01-gde-origen-organizacion.md](../decisiones/2026-06-01-gde-origen-organizacion.md)

## Resumen

Revierte la direccion del GDE introducida por #1605: ahora se carga desde el
Legajo de la Organizacion (unica fuente, solo en documentos `Aceptado`) y se
replica a las admisiones relacionadas.

## Cambios

- Org legajo:
  - Nueva columna "Número de GDE" en `organizacion_detail.html` + celda editable
    inline (cuando `Aceptado`) en el partial `documentacion_organizacion_row.html`
    (reusa la maquinaria inline existente de `organizacionesDocumentos.js`).
  - Endpoint `organizacion_documento_gde` (`actualizar_numero_gde_documento_organizacion`)
    + ruta. Valida `Aceptado` y permisos del legajo.
  - Helper `_render_fila_documentacion_y_row_id` (render unificado catalogo/personalizado);
    **estado y vencimiento ahora tambien soportan personalizados** (completa el Req 4).
- Replicacion: `AdmisionService.replicar_numero_gde_desde_organizacion` propaga el
  GDE a los `ArchivoAdmision` materializados (via `archivo_organizacion_origen`) de
  las admisiones activas y limpia el informe tecnico afectado.
- Admision-side: serializadores exponen `es_origen_organizacion`; en
  `documento_row.html` el GDE de documentos de origen organizacional queda
  solo-lectura. `actualizar_numero_gde_ajax` rechaza esos documentos.
- Migracion [0062_backfill_gde_a_organizacion.py](../../../admisiones/migrations/0062_backfill_gde_a_organizacion.py):
  backfill best-effort `NumeroGdeOrganizacion`/`ArchivoAdmision` -> `ArchivoOrganizacion.numero_gde`.

## Validacion

Entorno local Windows (venv Django 4.2.27, sqlite; Docker apagado):

- `pytest organizaciones/ admisiones/tests/` → 74 passed (incluye
  `test_gde_legajo_organizacion.py`: replicacion, rechazo no-aceptado, archivadas,
  guard admision-side).
- `manage.py makemigrations --check --dry-run admisiones organizaciones` → sin cambios.
- `manage.py migrate admisiones` (sqlite) → aplica 0062 OK.
- `black` + `djlint --check` sobre lo tocado → limpio.

## Riesgos

Ver la decision asociada: perdida de divergencia por-admision en el backfill
(conserva el mas reciente) y reinicio del informe tecnico de varias admisiones al
replicar. `NumeroGdeOrganizacion` se conserva como historico.
