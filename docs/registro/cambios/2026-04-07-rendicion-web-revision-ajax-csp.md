# Rendicion web: ajuste de revision AJAX y CSP

## Contexto

En el detalle web de rendiciones, la revision por documento ya funcionaba via
AJAX, pero quedaron dos problemas de UX y uno tecnico:

- al validar un documento, seguia visible la celda de revision con el selector
  y el boton verde;
- el boton de guardar no mostraba estado de carga mientras se enviaba;
- el template tenia `style=` y `<script>` inline que generaban advertencias CSP
  en consola.

## Cambio realizado

- Se corrigio el payload AJAX para enviar siempre `estado` y `observaciones`
  aunque los controles esten renderizados fuera del `<form>` y asociados con
  `form="..."`.
- Al guardar una revision exitosa, la celda `Revision` del documento pasa a
  `-`, tanto para filas principales como para filas de historial/subsanacion.
- El boton verde de guardar ahora muestra un spinner mientras la solicitud esta
  en curso.
- Se corrigio el mapeo de celdas `Estado` y `Revision` en las filas de
  subsanacion para que la actualizacion dinamica afecte la columna correcta.
- Se movio la logica JS del detalle a
  `static/custom/js/rendicioncuentasmensual_detail.js`.
- Se movieron los estilos puntuales del detalle a
  `static/custom/css/rendicioncuentasmensual_detail.css`.
- Se eliminaron del template los `style=` y el `<script>` inline para evitar
  advertencias CSP en esa pantalla.

## Validacion

- `docker compose exec django pytest tests/test_rendicioncuentasmensual_views_unit.py -q`
