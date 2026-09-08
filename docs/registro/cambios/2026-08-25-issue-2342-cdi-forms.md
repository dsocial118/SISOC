# 2026-08-25 - Issue 2342: referentes y formularios CDI

## Contexto

- El alta de un referente de CDI necesitaba solicitar y conservar DNI y CUIL al generar su usuario.
- La nómina permitía declarar discapacidad sin indicar un tipo y no incluía la opción explícita de no tener alergias alimentarias.
- Los formularios de trabajador aceptaban texto libre para departamento y el indicador de Cultura e identidad podía mostrar un estado incompleto aunque esa sección es opcional.

## Cambios aplicados

- Se agregaron DNI y CUIL opcionales al referente del CDI; se validan con las mismas reglas de `Mi cuenta`.
- Al generar un usuario referente de CDI ambos datos son obligatorios, se precargan para el primer referente y se guardan dentro de la misma transacción en `Profile.dni` y `Profile.cuil`.
- Se exige al menos un tipo de discapacidad cuando se responde afirmativamente que el niño/a tiene discapacidad.
- Se incorporó la opción no excluyente `No tiene alergias alimentarias`.
- El departamento de contacto del trabajador usa el catálogo `DepartamentoIpi` filtrado por provincia y conserva exclusivamente valores históricos durante su edición.
- El indicador de Cultura e identidad ya no informa incompleto un bloque opcional.

## Impacto esperado

- Las nuevas credenciales de referentes CDI quedan asociadas a su perfil sin afectar los demás flujos genéricos de creación delegada.
- La validación de discapacidad se aplica también ante envíos directos al servidor.
- El catálogo territorial evita nuevos departamentos de texto libre, manteniendo la edición de registros previos.

## Validación

- `pytest` focalizado en Docker: 117 tests de destinatarios, 15 de generación de usuarios CDI, 88 de formulario CDI y 70 de trabajadores, todos aprobados.
- `black --check` focalizado y `djlint --check` sobre los templates modificados, aprobados.
- `pylint` focalizado sobre los módulos Python modificados, 10.00/10.
- `python manage.py makemigrations --check --dry-run`, sin cambios detectados.
- Verificación de sintaxis JavaScript con `node --check` sobre los dos scripts modificados y `git diff --check`, aprobadas.

## Riesgos y rollback

- Requiere ejecutar la migración `0045_centrodeinfancia_dni_cuil_referente` antes de usar los campos del formulario CDI.
- Un valor histórico de departamento que no pertenezca al catálogo se conserva sólo si no se intenta reemplazar por otro valor fuera del catálogo.
- El rollback consiste en revertir este cambio; los campos nuevos son nulos y no requieren backfill.
