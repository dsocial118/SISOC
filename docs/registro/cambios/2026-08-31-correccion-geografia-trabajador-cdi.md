# Corrección del departamento de contacto en trabajadores CDI

## Problema

El desplegable de departamento enviaba el identificador numérico de
`DepartamentoIpi`, mientras que el campo histórico
`Trabajador.departamento_contacto` guarda y valida el nombre. Al guardar se
mostraba `Seleccione una opción válida. N no es una de las opciones disponibles.`

## Cambio

- El JavaScript del formulario usa el nombre como valor del departamento.
- El formulario del servidor normaliza también un ID válido de la provincia
  seleccionada al nombre persistido.
- Los IDs inexistentes o pertenecientes a otra provincia continúan rechazándose.

## Validación

- Regresión que reproduce el ID enviado por el desplegable.
- Suite completa de `test_trabajador_form.py`.
- Verificación sintáctica de `trabajadorForm.js` y formato Python.

