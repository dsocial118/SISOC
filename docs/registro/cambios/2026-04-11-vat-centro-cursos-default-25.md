# VAT centro detalle: cursos muestran 25 por defecto

Fecha: 2026-04-11

## Cambio aplicado

En la solapa `#cursos` del detalle de centros (`/vat/centros/<id>/`) el filtro `Ver`
de la tabla de cursos ahora inicia en `25` registros en lugar de `10`.

Tambien se alineo el boton `Limpiar` del filtro de cursos para que restablezca ese
mismo valor por defecto.

## Archivos involucrados

- `VAT/templates/vat/centros/partials/centro_cursos_panel.html`
- `VAT/templates/vat/centros/centro_detail.html`
- `VAT/tests.py`

## Validacion

- Test puntual del detalle/panel de cursos para verificar el default renderizado y
  el valor de reset del filtro.
