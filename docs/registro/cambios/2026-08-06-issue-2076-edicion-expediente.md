# Issue 2076: correccion de la carga de expedientes

## Problema

Los cuatro componentes del numero de expediente estaban declarados en un mixin que
Django no procesaba como formulario. Por eso no quedaban registrados en `form.fields`
y la pantalla de caratulacion no mostraba controles editables.

Ademas, las variantes que si tenian inputs los mostraban dentro de un solo
`input-group` en modales angostos. Los controles se comprimian hasta dificultar la
edicion tecnica y la rectificacion en Legales.

## Cambio

- El mixin incorpora explicitamente los cuatro campos a cada formulario.
- Los modales de expediente utilizan un ancho del 70% con maximo de 1000px y una grilla
  responsive alineada.
- Cada componente tiene etiqueta y ancho independiente.
- Ano y numero declaran teclado numerico, longitudes y placeholders.
- Reparticion y organismo se presentan en mayusculas.
- Caratulacion y Legales comparten un parcial para evitar diferencias visuales.
- Los errores por campo y de unicidad se muestran dentro del modal.

## Compatibilidad

No cambia el formato persistido: `EX-ANO-NUMERO- -APN-REPARTICION#ORGANISMO`.
