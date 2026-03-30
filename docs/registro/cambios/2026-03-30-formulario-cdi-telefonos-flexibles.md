# Formulario CDI: teléfonos con validación flexible

## Qué cambió

- Se alineó la validación de teléfonos de `FormularioCDIForm` con la del legajo `CentroDeInfancia`.
- Los campos `telefono_cdi`, `telefono_referente_cdi`, `telefono_organizacion` y `telefono_referente_organizacion` ahora aceptan números planos o grupos separados por guiones.
- Se agregaron tests de regresión para aceptar teléfonos flexibles y seguir rechazando caracteres inválidos.

## Problema que resuelve

El formulario CDI autocompletaba teléfonos desde el legajo del centro, pero luego rechazaba esos mismos datos por un validador más estricto definido en el modelo.

## Impacto esperado

- El usuario puede guardar el formulario CDI con teléfonos cargados desde el legajo sin reformatearlos.
- Se mantiene rechazo para valores con letras u otros caracteres no válidos.
