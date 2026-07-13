# Layout principal con sidebar sticky

## Cambio

- La barra lateral de escritorio deja de usar posicionamiento fijo y pasa a
  permanecer visible mediante `position: sticky` debajo del encabezado.
- El contenido principal deja de compensar manualmente el ancho y la altura de
  la barra lateral; sidebar, main y footer vuelven a distribuirse mediante la
  grilla principal de AdminLTE.
- Sidebar y main comparten la primera fila de la grilla; el footer permanece en
  el flujo normal, ocupa una segunda fila de ancho completo y no se superpone
  con la barra lateral.
- En pantallas menores a `992px` se conserva el comportamiento off-canvas de
  AdminLTE para la navegación lateral.

## Validación esperada

- En escritorio, al desplazarse verticalmente, la barra lateral queda debajo
  del encabezado y su contenido puede desplazarse internamente.
- Al contraer la barra lateral, main y footer se adaptan al ancho disponible.
- En páginas cortas, el footer se mantiene al pie de la ventana; en páginas
  largas aparece después del contenido sin superponerse.
