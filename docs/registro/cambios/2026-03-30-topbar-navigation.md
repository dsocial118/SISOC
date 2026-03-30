# 2026-03-30 - migración inicial de sidebar a topbar pura

## Resumen

Se reemplazó la navegación lateral fija por una navegación principal en topbar para desktop y un offcanvas para mobile.

## Cambios principales

- Se agregó un CSS compartido para layout y dropdowns de topbar.
- Se agregó un JS pequeño para apertura/cierre de menús superiores.
- `includes/header.html` y `includes/new_navbar.html` pasaron a renderizar navegación principal horizontal.
- `includes/sidebar/base.html` y `includes/sidebar/new_base.html` dejaron de renderizar un lateral fijo y ahora exponen navegación mobile temporal.
- `base.html` y `new_base.html` dejaron de depender de clases de layout lateral permanente.

## Impacto esperado

- Más ancho disponible para vistas operativas.
- Menor dependencia de colapso lateral.
- Navegación principal más visible en desktop.

## Limitaciones

- La estructura de menús complejos sigue basada en los parciales existentes.
- Puede requerirse un ajuste visual posterior por módulo si algún submenu queda demasiado extenso.
