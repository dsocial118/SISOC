# 2026-04-08 - Credenciales masivas: mail destino desacoplado del usuario

## Contexto

En el envio masivo de credenciales aparecieron dos casos operativos reales:

- filas cuyo mail llega vacio;
- distintos usuarios que deben recibir el correo en un mismo mail de destino.

La implementacion anterior trataba el mail del Excel como dato a sincronizar en
`user.email`, validaba unicidad y podia rechazar escenarios validos para la
operacion.

## Cambio aplicado

- El mail de la planilla pasa a ser exclusivamente el **destino del envio**.
- Ya no se actualiza `user.email` durante el procesamiento masivo.
- Ya no se valida unicidad del mail contra otros usuarios.
- Si una fila llega sin mail, la fila se rechaza y queda reportada en el
  resumen, pero el lote continua con el resto.
- El resumen por fila ahora muestra `Mail destino` en lugar de `Mail actualizado`.
- El conteo de `Actualizados` refleja solo cambios de password.

## Validacion

- `USE_SQLITE_FOR_TESTS=1 python -m pytest tests/test_users_bulk_credentials.py -q`
- `python -m black --check users\\services_bulk_credentials.py users\\services.py tests\\test_users_bulk_credentials.py`
- `djlint users\\templates\\user\\bulk_credentials_form.html --check --configuration=.djlintrc`

## Supuesto

El mail informado en el Excel representa el canal operativo de envio para esa
fila, aunque no coincida con el mail persistido en el usuario o aunque sea
compartido por varios usuarios.
