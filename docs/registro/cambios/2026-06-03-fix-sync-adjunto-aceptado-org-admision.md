# 2026-06-03 — Fix: "Actualizar desde Legajo" no refrescaba el adjunto cuando el doc estaba Aceptado

Issue relacionado: [#1799](https://github.com/dsocial118/SISOC/issues/1799) (seguimiento de la
sincronización de documentación Organización → Admisión).

## Problema

Al **actualizar un archivo adjunto en la Organización** y luego pedir "Actualizar
Información desde Legajo Organización" en la Admisión, la admisión **seguía
mostrando el adjunto viejo**.

Causa raíz en
[`AdmisionService.actualizar_documentacion_desde_organizacion`](../../../admisiones/services/admisiones_service/impl.py)
(actualización dirigida del #1799 feedback punto 1): el bucle de borrado **saltaba
incondicionalmente** todo `ArchivoAdmision` de origen organizacional con estado
`"Aceptado"`. Ese salto existía para no pisar una validación admisión-side ante
cambios de metadatos (estado/observaciones). Pero un documento organizacional
validado se clona en la admisión **con estado `Aceptado`**, y cuando la
organización sube un adjunto nuevo sobre un doc Aceptado el flujo real crea una
**nueva versión** (`ArchivoOrganizacion` vigente,
[`organizaciones/views.py:subir_documento_organizacion`](../../../organizaciones/views.py)).
Resultado: el cambio se detectaba (el token difería) pero la copia Aceptada no se
borraba, y `congelar_documentacion_organizacional` no la re-creaba (ya existía) →
adjunto viejo persistente.

## Solución

Preservar el documento Aceptado **solo si el archivo del legajo no cambió**. Si la
organización subió un adjunto nuevo (cambió el nombre del archivo vigente respecto
de la copia materializada), la validación quedó obsoleta y el documento se
refresca. Los cambios que solo tocan metadatos (estado/observaciones/vencimiento)
siguen preservando la validación.

- Se construye un mapa `slot -> nombre de archivo vigente` del legajo y se compara
  contra el `archivo.name` de la copia materializada. Es un discriminante seguro:
  los documentos de origen organizacional son **solo lectura admisión-side**
  (ver `admisiones/tests/test_gde_cell_ajax.py::test_doc_origen_organizacion_aceptado_es_solo_lectura`),
  así que el nombre de archivo de la copia refleja el archivo del legajo al momento
  del clonado.

## Tests

[admisiones/tests/test_actualizar_documentacion_dirigido.py](../../../admisiones/tests/test_actualizar_documentacion_dirigido.py)

- **Nuevo** `test_actualizar_refresca_doc_aceptado_cuando_cambia_el_archivo`: doc
  org Aceptado en la admisión + la organización sube un adjunto nuevo (nueva
  versión vigente) → la admisión muestra ahora el archivo nuevo.
- Regresión `test_actualizar_preserva_doc_aceptado_de_origen_org` (cambio de solo
  metadatos preserva la validación) sigue verde.

Validación local (Docker, SQLite): `test_actualizar_documentacion_dirigido.py`
5 passed; suite de doc-sync de admisiones (resync + desactualizada +
archivo_organizacion_origen + gde_cell + dirigido) 30 passed; `black --check` OK.
