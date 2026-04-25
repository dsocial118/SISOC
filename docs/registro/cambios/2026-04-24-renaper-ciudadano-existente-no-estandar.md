# RENAPER en busqueda de ciudadano existente no estandar

## Contexto

Al registrar un ciudadano desde la busqueda por DNI, si ya existian registros con
ese DNI pero ninguno estaba validado como `ESTANDAR`, la vista avisaba la
coincidencia y cortaba el flujo antes de consultar RENAPER.

## Cambio

La busqueda mantiene el aviso sobre registros previos no estandar, pero continua
con la consulta RENAPER para precargar el formulario cuando el servicio devuelve
datos validos.

## Impacto

- Permite contrastar el registro previo con datos actuales de RENAPER.
- Evita la carga manual completa cuando el DNI ya existe solo en registros que
  requieren revision de identidad.
- No cambia el comportamiento cuando ya existe un ciudadano `ESTANDAR`: se sigue
  redirigiendo a su legajo para edicion.
