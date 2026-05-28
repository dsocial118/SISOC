# Primer seguimiento de relevamientos

## Contexto

El relevamiento actual queda como `Relevamiento inicial`. El primer seguimiento debe crearse desde el mismo modal, vinculado al ultimo relevamiento activo del comedor, sin enviar un relevamiento inicial nuevo a GESTIONAR cuando el ancla se crea solo por necesidad tecnica.

## Cambio

- Se agrega `PrimerSeguimiento` y sus bloques relacionados en `relevamientos`.
- Se incorpora `PrimerSeguimientoService` para resolver o crear el ancla local, bloquear duplicados y disparar el sync especifico.
- Se agrega `PATCH /api/relevamiento/primer-seguimiento` con validacion de `sisoc_id` e `id_relevamiento`.
- El modal de relevamientos suma `tipo_relevamiento` y deja `Segundo seguimiento` rechazado hasta fase 2.
- Se agregan variables `GESTIONAR_API_CREAR_PRIMER_SEGUIMIENTO` y `GESTIONAR_API_BORRAR_PRIMER_SEGUIMIENTO`.

## Decisiones

- `Relevamiento` sigue siendo el ancla del flujo existente.
- El `cod_pnud` del seguimiento se deriva desde `id_relevamiento.comedor.codigo_de_proyecto`.
- Los choices sin catalogo confirmado se mantienen como texto flexible.
- Las firmas se guardan como string/URL porque el payload externo no trae carga binaria.
