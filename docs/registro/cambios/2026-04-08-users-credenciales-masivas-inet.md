# 2026-04-08 - Credenciales masivas: variante INET y selector de tipo

## Contexto

El flujo inicial de envio masivo de credenciales en `users` solo soportaba un formato de Excel y un unico template de correo. El equipo necesitaba incorporar una variante `INET`, con una columna extra `Nombre del Centro` y un correo distinto al envio estandar.

## Cambio aplicado

- Se agrego un desplegable `tipo_envio` en la pantalla de credenciales masivas.
- El backend ahora resuelve por tipo:
  - columnas requeridas;
  - plantilla Excel descargable;
  - subject del correo;
  - template de mail.
- Se mantiene el tipo `Estandar` con las columnas originales `usuario`, `mail`, `password`.
- Se agrega el tipo `INET` con columnas `usuario`, `mail`, `password`, `Nombre del Centro`.
- El boton `Descargar plantilla` reutiliza el tipo seleccionado para bajar el Excel correcto sin abrir un flujo separado.
- El correo `INET` usa un template propio con saludo por centro, acceso a la plataforma, agenda de capacitaciones y video de referencia.
- El asunto del correo `INET` se toma literal del documento provisto por el equipo: `Acceso a la plataforma y capacitación virtual – INET`.
- Se actualizo el cuerpo `INET` segun `Template Sisoc (1).docx`, incluyendo la aclaracion de temas comunes, el link corto actualizado del video y el cierre `Nos vemos pronto`.

## Validacion

- `python -m black --check users\\forms.py users\\views.py users\\services_bulk_credentials.py tests\\test_users_bulk_credentials.py`
- `USE_SQLITE_FOR_TESTS=1 python -m pytest tests\\test_users_bulk_credentials.py -q`

## Supuesto

- Las fechas, links, asunto y datos de capacitacion del template `INET` se toman del `.docx` provisto por el equipo y quedan hardcodeados en esta iteracion.
