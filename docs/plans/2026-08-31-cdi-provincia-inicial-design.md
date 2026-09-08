# Diseño: provincia inicial en altas CDI

## Objetivo

Al iniciar un alta de nómina o de trabajador en un CDI, seleccionar como valor
inicial la provincia del CDI. El campo permanece editable.

## Alcance

- `NominaCentroInfanciaCreateView`: `provincia_domicilio`.
- `TrabajadorCentroInfanciaCreateView`: `provincia_contacto`.
- Solo altas; las ediciones conservan los valores históricos.
- No se precargan departamento, municipio ni localidad.

## Comportamiento

Cuando el CDI tiene provincia, esta prevalece sobre cualquier dato territorial
precargado desde un ciudadano o RENAPER. Se eliminan los valores iniciales de
los campos dependientes para que la cascada existente cargue opciones coherentes
con la provincia elegida. Si el CDI no tiene provincia, no se modifica el
comportamiento actual.

## Implementación y validación

Una utilidad privada de vistas compone el diccionario inicial para ambos flujos.
Las pruebas de integración verificarán la provincia inicial, la ausencia de
precarga en los campos dependientes y el fallback cuando el CDI no tenga
provincia.
