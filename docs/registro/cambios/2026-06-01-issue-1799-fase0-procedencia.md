# 2026-06-01 — Issue #1799 (Fase 0): procedencia de documentacion materializada

Rama: `claude/issue-1799-fase0-procedencia`
Plan: [docs/plans/2026-06-01-issue-1799-documentacion-organizacion-admisiones.md](../../plans/2026-06-01-issue-1799-documentacion-organizacion-admisiones.md)

## Resumen

Fase fundacional del issue #1799 (sin cambios de comportamiento visibles). Agrega
trazabilidad explicita entre un `ArchivoAdmision` materializado y el
`ArchivoOrganizacion` del legajo del que proviene. Esta procedencia la consumiran
las fases posteriores:

- **Req 3 (GDE):** replicar el Numero de GDE del legajo a las admisiones de forma
  exacta (sin depender del matching por nombre).
- **Req 1 (advertencia):** detectar que documentos del legajo cambiaron respecto de
  lo que la admision ya tenia.

## Cambios

- Modelo: nuevo campo `ArchivoAdmision.archivo_organizacion_origen`
  (FK a `organizaciones.ArchivoOrganizacion`, `on_delete=SET_NULL`, nullable).
- Servicio: `_crear_archivo_admision_desde_archivo_organizacion` setea la FK al
  materializar (ya recibia el `ArchivoOrganizacion` de origen).
- Migracion [0061_archivoadmision_archivo_organizacion_origen.py](../../../admisiones/migrations/0061_archivoadmision_archivo_organizacion_origen.py):
  AddField + backfill best-effort. El backfill aprovecha que al materializar se
  copia `archivo=archivo_org.archivo.name`, por lo que el nombre de archivo
  coincide EXACTAMENTE con el origen dentro de la misma organizacion; se usa esa
  coincidencia como join (solo si hay exactamente una coincidencia).

## Validacion

Entorno local Windows (venv con Django 4.2.27, sqlite para tests; Docker apagado):

- `pytest admisiones/tests/test_archivo_organizacion_origen.py admisiones/tests/test_numero_gde_organizacion.py admisiones/tests/test_resync_admision.py` → 16 passed.
- `manage.py makemigrations --check --dry-run admisiones organizaciones` → sin cambios.
- `manage.py migrate admisiones` (sqlite) → aplica 0061 + backfill sin error.

Nota: el `migrate` completo del proyecto en sqlite falla por una migracion
preexistente NO relacionada (`NewActividadCentro has no field 'centro'`), ajena a
este cambio. La validacion se acoto a las apps afectadas.

## Riesgos

- Backfill best-effort: si un mismo nombre de archivo aparece en >1
  `ArchivoOrganizacion` de la misma organizacion, no se asocia (se evita
  ambiguedad). Los `ArchivoAdmision` sin match quedan con la FK en `NULL` (el
  matching por nombre del flujo actual sigue funcionando como fallback).
