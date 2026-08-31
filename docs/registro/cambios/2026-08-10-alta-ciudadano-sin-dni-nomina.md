# Alta de ciudadano sin DNI desde nómina

Se agregó una alternativa **Sin DNI** en la pantalla de creación de ciudadanos
de la nómina. La interfaz conserva el formulario con DNI y muestra un único
formulario por vez.

Exclusivamente los ciudadanos sin DNI creados por esta vía se guardan con
`requiere_revision_manual = false` y se incorporan directamente a la nómina.
Las altas sin DNI realizadas desde cualquier otro flujo conservan la revisión
manual obligatoria.

Además, el modal para incorporar a un ciudadano encontrado permite completar y
guardar `pertenece_comunidad_indigena`, `en_situacion_de_calle` y
`persona_con_celiaquia` sobre el registro seleccionado.

La incorporación a la nómina y la actualización de esos datos se ejecutan en
una única transacción. Si falla cualquiera de las dos escrituras, ambas se
revierten.
