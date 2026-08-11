# Estabilidad visual de Select2 en el formulario de comedores

## Cambio

Los Select2 del alta y la edición de comedores ya no modifican el `overflow` del
documento ni del contenedor principal cuando se despliegan. El buscador del
dropdown conserva el autoenfoque, pero usa `preventScroll` para no desplazar el
contenido ni el sidebar.

## Motivo

La combinación de bloquear el scroll del `body` y forzar `overflow: visible` en
`.app-content` interfería con el layout fijo de AdminLTE. Al abrir un selector,
partes del sidebar y del formulario podían quedar fuera del área visible.

## Alcance

El ajuste se limita a `comedorFormModerno.css` y `comedorFormModerno.js`, cargados
por `comedor/comedor_form.html`. No cambia la lógica de creación o edición ni los
datos enviados por el formulario.
