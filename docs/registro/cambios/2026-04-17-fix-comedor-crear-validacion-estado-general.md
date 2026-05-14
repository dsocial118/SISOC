# Comedores crear: revalidacion visual de estado general

Fecha: 2026-04-17

## Contexto

En `/comedores/crear`, el `select` de `Estado general` podia quedar en rojo
despues de elegir una opcion valida. El problema era visual: la capa de
validacion en tiempo real no se enteraba del cambio cuando el campo estaba
envuelto por Select2.

## Cambio aplicado

- Se extrajo un helper para resolver el wrapper visual del campo.
- La validacion en tiempo real ahora escucha `change` y eventos `select2` sobre
  el `<select>` real, en lugar de depender de un selector `.select2` que no
  cubria el caso.
- Los campos requeridos deshabilitados dejan de conservar estados visuales
  viejos (`valid` o `invalid`).

## Decision clave

La correccion se hizo solo en `static/custom/js/comedorFormModerno.js`, porque
la causa raiz estaba en la logica de validacion del frontend y no en
`ComedorForm` ni en la validacion server-side.

## Validacion

- `node --check static/custom/js/comedorFormModerno.js`
- Smoke ejecutable en Node con stubs minimos para verificar que un `select`
  requerido pasa de `invalid` a `valid` al disparar `change/select2:select`.
