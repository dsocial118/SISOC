# Fix: Sidebar vuelve a estado desktop al maximizar ventana

**Fecha:** 2026-03-26
**Tipo:** Bugfix UI/Responsive
**Área:** Layout / navegación lateral

## Problema
Al reducir la ventana (modo mobile) y luego volver a maximizar, el sidebar conservaba estado móvil y no recuperaba el comportamiento visual correcto de desktop.

## Causa raíz
El estado del sidebar quedaba condicionado por clases/residuos de modo mobile (`sidebar-open`, `sidebar-collapse`, estilos inline y overlay), sin una normalización explícita al volver a desktop.

## Solución implementada
Se agregó sincronización en `static/custom/js/base.js` basada en la visibilidad del botón mobile de sidebar:

- Referencia de viewport desktop/mobile:
  - Selector: `[data-lte-toggle="sidebar"].d-lg-none`
  - Si el botón está oculto (`display: none`), se considera desktop.
- En desktop:
  - Se remueve `sidebar-open` y `sidebar-collapse` del `body`.
  - Se limpian clases/estilos residuales en `.app-sidebar` (`show`, `sidebar-open`, `margin-left`).
  - Se elimina `.sidebar-overlay` residual.
- Se ejecuta al cargar y en `resize` (con `setTimeout(..., 0)` para sincronizar con el ciclo del layout).

## Archivo modificado
- `static/custom/js/base.js`

## Validación manual
1. En desktop: sidebar visible/expandido correctamente.
2. Reducir ventana hasta que aparezca botón mobile en header.
3. Abrir/cerrar sidebar en mobile.
4. Maximizar nuevamente.
5. Verificar que el sidebar vuelve al estado desktop correcto y no queda en modo mobile.

## Riesgo / rollback
- Riesgo bajo (cambio acotado al manejo de clases CSS del sidebar).
- Rollback: revertir cambios en `static/custom/js/base.js`.
