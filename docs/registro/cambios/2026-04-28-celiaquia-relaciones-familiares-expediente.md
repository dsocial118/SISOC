# Celiaquia: relaciones familiares en detalle de expediente

## Contexto

El detalle de un expediente de Celiaquia muestra la jerarquia familiar de sus
legajos. Las relaciones familiares se guardan de forma global en
`ciudadanos_grupofamiliar`, por ciudadano, y pueden existir aunque una de las
personas no pertenezca al expediente que se esta consultando.

## Cambio

Para el arbol visual del expediente y el calculo de responsable efectivo, solo
cuentan las relaciones donde ambos ciudadanos tienen legajo activo dentro del
mismo expediente.

Esto evita dos casos confusos:

- un beneficiario aparece indentado porque tiene responsable global fuera del
  expediente;
- un beneficiario aparece como responsable efectivo porque tiene hijos globales
  fuera del expediente.

## Impacto

La relacion familiar global no se borra ni se modifica. El cambio solo acota la
interpretacion dentro del detalle del expediente y de los helpers que calculan
responsables para legajos del expediente.
