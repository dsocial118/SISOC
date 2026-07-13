# VAT: cascada Municipio → Localidad rota en crear/editar centro

## Contexto (bug reportado)

En el formulario de alta/edicion de centro, al cambiar el Municipio el select
de Localidad no actualizaba sus opciones: seguia mostrando las localidades del
municipio anterior. Mas visible en edicion, donde el form filtra las
localidades por el municipio original de la instancia.

## Diagnostico

Bug clasico de Select2 + JS vanilla:

- Los selects de provincia/municipio/localidad llevan clase `select2`
  (`_select2_attrs` en `VAT/forms.py`) y `custom.js` los inicializa
  globalmente.
- Al elegir una opcion, Select2 dispara un evento `change` **de jQuery**, que
  no ejecuta listeners nativos registrados con `addEventListener`.
- `static/custom/js/centro_create_form.js` bindeaba la cascada
  (provincia→municipio y municipio→localidad) con `addEventListener("change")`
  → los handlers nunca corrian y las opciones no se recargaban.

## Cambio

`centro_create_form.js`: nuevo helper `bindSelectChange()` que bindea via
jQuery cuando esta disponible (los handlers jQuery reciben tanto el change de
Select2 como el nativo) con fallback a `addEventListener`. Se aplica a ambos
eslabones de la cascada.

## Validacion

Verificacion E2E con Playwright sobre la pagina real de edicion
(`/vat/centros/<id>/editar/` en el stack local, sesion autenticada):

- Antes del cambio de municipio: opciones de localidad = las del municipio
  original.
- Se simula la seleccion de otro municipio exactamente como lo hace Select2
  (`$('#id_municipio').val(x).trigger('change')`).
- Resultado: el select de Localidad recarga con las localidades del municipio
  nuevo y desaparecen las del anterior (`CASCADA OK`).
