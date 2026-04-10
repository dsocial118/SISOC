# 2026-04-10 - Credenciales masivas: Excel solo por usuario

## Contexto

El envio masivo de credenciales necesitaba dejar de depender de mails y
passwords cargados manualmente en el Excel. Esos datos generan dos riesgos:

- el mail de destino puede no coincidir con el usuario real o estar vacio;
- la password del Excel puede forzar cambios no deseados o quedar desalineada
  con la credencial vigente del usuario.

## Cambio aplicado

- La planilla estandar ahora requiere solo la columna `usuario`.
- La planilla `INET` requiere `usuario` y `Nombre del Centro`.
- El mail destino se resuelve desde `user.email`.
- El proceso ya no actualiza `user.email`.
- El proceso ya no actualiza ni valida passwords recibidas por Excel.
- La password enviada se toma de `Profile.temporary_password_plaintext`.
- Si el usuario no tiene mail cargado, mail valido o contraseña temporal visible,
  la fila queda rechazada con causa explicita y sin side effects.
- Los resultados persistidos de lote mantienen el mail destino usado para los
  envios exitosos.

## Decision de seguridad

Django no permite recuperar una contraseña real desde el hash guardado en
`User.password`. Por eso, el flujo solo puede enviar credenciales cuando existe
una contraseña temporal visible persistida en `Profile.temporary_password_plaintext`.
Si ese dato no existe, no se genera una nueva password automaticamente en este
flujo: la fila se rechaza para evitar cambiar credenciales sin una accion
administrativa explicita.

## Validacion prevista

- `python -m pytest tests/test_users_bulk_credentials.py -q`
- `python -m black --check users/services_bulk_credentials.py users/services_bulk_credentials_jobs.py users/services.py tests/test_users_bulk_credentials.py`
- `djlint users/templates/user/bulk_credentials_form.html users/templates/user/bulk_credentials_job_detail.html --check --configuration=.djlintrc`
