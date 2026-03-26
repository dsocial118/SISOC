# 2026-03-26 - Alta de relevamiento desde listado

## Resumen
- Se recupero el flujo de alta de relevamiento desde `comedores/<pk>/relevamiento/listar`.
- El boton `Agregar` vuelve a abrir un modal para crear el relevamiento.
- La creacion usa el endpoint existente `relevamiento_create_edit_ajax` y mantiene la logica de territorial opcional.

## Cambios realizados
- Archivo: `relevamientos/templates/relevamiento_list.html`
  - Se reemplazo el link de `Agregar` por un boton que abre `#modalRelevamientoNuevo`.
  - Se agrego modal con formulario `POST` a `relevamiento_create_edit_ajax`.
  - Se incorporo select `new_territorial_select` para cargar territoriales.
  - Se reutilizo `static/custom/js/comedordetail_territorial_cache.js` para poblar territoriales desde cache/API.
- Archivo: `relevamientos/tests.py`
  - Se agregaron pruebas para verificar render del modal y alta efectiva con territorial desde el listado.

## Comportamiento observable
- En `relevamiento/listar`, usuarios con permiso de alta ven el boton `Agregar`.
- Al crear desde el modal:
  - con territorial, el relevamiento queda en estado `Visita pendiente`;
  - sin territorial, el servicio conserva el comportamiento previo (`Pendiente`).
