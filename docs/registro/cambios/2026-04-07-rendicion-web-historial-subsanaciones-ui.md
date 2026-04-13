# Rendicion web: menor peso visual para historial de subsanaciones

## Contexto

En el detalle web de rendiciones, para `Comprobantes` y `Documentacion Extra`
el historial de archivos observados seguia mostrandose mezclado junto a los
archivos vigentes. Eso hacia que el usuario confundiera los archivos nuevos
subidos en mobile con los anteriores que ya habian quedado observados.

## Cambio realizado

- En `Comprobantes` y `Documentacion Extra`, las filas de historial ahora se
  renderizan al final del bloque de la categoria.
- Se agrega un separador visual `Archivos anteriores observados`.
- El estado del historial deja de mostrarse como badge fuerte y pasa a verse
  como texto sutil.
- Las filas historicas quedan con menor peso visual para priorizar los
  documentos vigentes del grupo.

## Validacion

- Validacion manual pendiente en el detalle web de rendicion.
