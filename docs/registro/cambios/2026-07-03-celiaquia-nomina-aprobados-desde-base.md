# 2026-07-03 - Celiaquía: nómina de aprobados se genera desde la base

## Qué cambió

- La descarga "Descargar nómina aprobados" (`ExpedientePadronFinalExportView`) ahora construye
  el Excel desde la base de datos: legajos con `revision_tecnico=APROBADO` y
  `resultado_sintys=MATCH`, excluyendo responsables puros (`rol=responsable`). Antes tomaba el
  Excel original cargado por la provincia (`excel_masivo`) y filtraba sus filas comparando la
  columna documento contra los documentos de la base.
- Los datos del responsable (cuidador principal en `GrupoFamiliar`) se vuelcan en las columnas
  `*_RESPONSABLE` de la fila de cada beneficiario.
- Municipio y localidad se exportan por nombre (antes quedaba el código/ID que traía el Excel
  original).
- La descarga ya no exige que exista `excel_masivo` (vista y contexto del detalle), solo estado
  `CRUCE_FINALIZADO`.

## Causa raíz / decisión clave

- Caso real (expediente 223, Tucumán): un beneficiario aprobado y con MATCH no aparecía en la
  descarga. Su documento venía mal tipeado en el Excel original (`2055724691`, CUIT sin el
  último dígito); al corregirse en la base (`20557246918`), el filtro contra el archivo estático
  dejaba de matchear y la fila desaparecía del export. El cruce con Sintys sí lo aprobaba porque
  para beneficiarios con responsable valida el CUIT del responsable.
- Decisión: la base es la fuente de verdad. El Excel original queda estático mientras los datos
  se corrigen después de la importación (documentos, RENAPER, subsanaciones), por lo que
  cualquier corrección posterior rompía el filtro. Generar desde la base hace que la nómina
  refleje siempre el estado actual.
- El layout de columnas se mantiene igual al de la plantilla de importación
  (`NOMINA_HEADERS` en `padron_final_service`), para no romper a los consumidores del archivo.

## Archivos tocados

- `celiaquia/services/padron_final_service/impl.py`
- `celiaquia/views/padron_final_export.py`
- `celiaquia/views/expediente.py` (contexto `can_download_nomina_aprobados`)
- `celiaquia/tests/test_padron_final_export.py`

## Validación

- `pytest celiaquia/tests/test_padron_final_export.py` + `test_nomina_sintys_export.py` +
  `test_cruce_service.py`: 11 passed. Fallan 2 tests de render de vistas por incompatibilidad
  preexistente del entorno local (Python 3.14 + Django 4.2 en el test client); fallan igual sin
  estos cambios.
- Verificación end-to-end contra datos reales (expediente 223): 36 filas (coincide con los
  36 beneficiarios APROBADO+MATCH de la base), el beneficiario del caso reportado aparece con
  su responsable y CUIT, y municipio/localidad salen con nombre.
