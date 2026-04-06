# Centro de infancia: edición con resaltado de campos inválidos

## Qué cambió

- Se desactivó la validación nativa del navegador en el form de legajo CDI para que la validación custom del frontend pueda marcar los campos requeridos.
- Se agregó una alerta general cuando el backend devuelve errores de formulario.
- Se incorporó una regresión de view/template para asegurar que la edición renderiza `novalidate` y conserva los `required` de los teléfonos.

## Problema que resuelve

En edición, al intentar guardar un legajo sin completar campos requeridos, el navegador podía interceptar el submit antes de que el JS del proyecto aplicara el resaltado visual de errores.

## Impacto esperado

- Al guardar con campos requeridos vacíos, el formulario vuelve mostrando el mensaje general y los campos inválidos resaltados por la validación custom del proyecto.
