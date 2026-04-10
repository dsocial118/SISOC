# 2026-04-10 - Credenciales masivas: Excel con usuario y mail destino

## Contexto

El envio masivo de credenciales necesitaba dejar de depender de passwords
cargadas manualmente en el Excel, pero mantener un mail operativo de destino por
fila. El mail informado por el operador puede no coincidir con el mail
persistido en el usuario y aun asi debe usarse para el envio.

Riesgos cubiertos:

- la password del Excel puede forzar cambios no deseados o quedar desalineada
  con la credencial vigente del usuario;
- actualizar `user.email` desde una planilla operativa puede pisar datos del
  usuario sin que ese sea el objetivo del lote.

## Cambio aplicado

- La planilla estandar ahora requiere las columnas `usuario` y `mail`.
- La planilla `INET` requiere `usuario`, `mail` y `Nombre del Centro`.
- El mail destino se resuelve desde la columna `mail` del Excel cuando viene
  informada.
- Si la celda `mail` esta vacia, se usa `user.email` como fallback.
- El proceso ya no actualiza `user.email`.
- El proceso ya no actualiza ni valida passwords recibidas por Excel.
- La password enviada se toma de `Profile.temporary_password_plaintext`.
- Si la fila no tiene mail y el usuario tampoco tiene un mail cargado, si el
  mail resultante es invalido, o si el usuario no tiene contrasena temporal
  visible, la fila queda rechazada con causa explicita y sin side effects.
- Los resultados persistidos de lote mantienen el mail destino usado para los
  envios exitosos.

## Decision de seguridad

Django no permite recuperar una contrasena real desde el hash guardado en
`User.password`. Por eso, el flujo solo puede enviar credenciales cuando existe
una contrasena temporal visible persistida en `Profile.temporary_password_plaintext`.
Si ese dato no existe, no se genera una nueva password automaticamente en este
flujo: la fila se rechaza para evitar cambiar credenciales sin una accion
administrativa explicita.

## Validacion prevista

- `python -m pytest tests/test_users_bulk_credentials.py -q`
- `python -m black --check users/services_bulk_credentials.py users/services_bulk_credentials_jobs.py users/services.py tests/test_users_bulk_credentials.py`
- `djlint users/templates/user/bulk_credentials_form.html users/templates/user/bulk_credentials_job_detail.html --check --configuration=.djlintrc`
