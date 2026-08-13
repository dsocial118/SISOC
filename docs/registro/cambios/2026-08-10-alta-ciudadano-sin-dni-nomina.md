# Alta de ciudadano sin DNI desde nómina

Se agregó una alternativa **Sin DNI** en la pantalla de creación de ciudadanos
de la nómina. La interfaz conserva el formulario con DNI y muestra un único
formulario por vez.

Exclusivamente los ciudadanos sin DNI creados por esta vía se guardan con
`requiere_revision_manual = false` y se incorporan directamente a la nómina.
Las altas sin DNI realizadas desde cualquier otro flujo conservan la revisión
manual obligatoria.
