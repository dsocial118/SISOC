# 2026-06-02 — Issue #1799 (feedback punto 4): el campo "Número de GDE" no aparecía en docs de la Admisión

Rama: `claude/issue-1799-fix-gde-ajax-render`
Issue: [#1799](https://github.com/dsocial118/SISOC/issues/1799) (comentario 2026-06-02, punto 4)

## Problema

El revisor reportó que el campo `Número de GDE` se visualiza para los documentos
de la Organización pero **no para los documentos de la Admisión**.

**Causa raíz (client-side):** el render server-side ya era correcto
(`documento_row.html` muestra un campo GDE editable para documentos nativos en
estado `Aceptado`). El problema aparecía al **aceptar un documento en la misma
sesión** vía el `<select>` inline: `actualizarEstado()`
([static/custom/js/admisionesactualizarestado.js](../../../static/custom/js/admisionesactualizarestado.js))
re-renderizaba **solo** la celda de estado (`displayState`) y **nunca tocaba la
celda GDE** (`gde-{id}`). Resultado: el badge pasaba a "Aceptado" pero la celda
GDE conservaba el `-` renderizado cuando el documento estaba `Pendiente`; el campo
recién aparecía al recargar la página. Los documentos de la Organización "se ven"
porque llegan ya `Aceptado` desde el Legajo (render server-side).

## Solución

Re-renderizar la celda GDE en el mismo flujo AJAX, reusando la lógica server-side
(sin duplicar permisos/origen en JS):

- **Partial** [admisiones/templates/admisiones/includes/gde_cell.html](../../../admisiones/templates/admisiones/includes/gde_cell.html):
  se extrae el interior del `<td id="gde-...">` a un include reutilizable.
  `documento_row.html` ahora lo incluye (sin cambio visual).
- **Servicio** `AdmisionService._render_celda_gde_html(archivo, request)` +
  `gde_html` en `_build_success_actualizar_estado_ajax_response`
  ([admisiones/services/admisiones_service/impl.py](../../../admisiones/services/admisiones_service/impl.py)):
  serializa el `ArchivoAdmision` (`_serialize_documentacion` o
  `serialize_documento_personalizado`) y renderiza el partial con `render_to_string`.
- **Vista** `actualizar_estado_archivo`
  ([admisiones/views/web_views.py](../../../admisiones/views/web_views.py)):
  reenvía `gde_html` en el JSON de éxito.
- **JS**: al recibir la respuesta, si viene `gde_html` se inyecta en
  `#gde-{documentoId}`. Los `data-call-click` del widget funcionan por delegación
  de eventos ([base.js](../../../static/custom/js/base.js)), así que el campo queda
  operativo sin re-binding.

Documentos de origen organizacional siguen en **solo lectura** admisión-side
(el GDE se gestiona desde el Legajo, #1799 Req 3).

## Validación

Entorno local Windows (Docker apagado, ver memoria de validación):

- `python -m py_compile` sobre impl.py / web_views.py / test → OK.
- `python -m black --check` sobre los .py → sin cambios.
- `python -m djlint --reformat` sobre los templates → canónicos.
- Tests nuevos: [admisiones/tests/test_gde_cell_ajax.py](../../../admisiones/tests/test_gde_cell_ajax.py)
  (doc nativo aceptado → campo editable; doc origen-org → solo lectura; no aceptado
  → `-`). Corren en la CI del PR (pytest local requiere Docker).

Manual: aceptar un documento nativo de la admisión → el campo `Número de GDE`
aparece sin recargar la página.
