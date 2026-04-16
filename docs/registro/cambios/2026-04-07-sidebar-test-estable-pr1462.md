# Estabilización del test del sidebar para la reorganización del menú

## Contexto

El test agregado para validar la reorganización del menú principal dependía de la versión exacta publicada en `CHANGELOG.md` y de una cadena inline de estilos completa.

## Cambio realizado

- Se ajustó `core/tests/test_sidebar_menu.py` para seguir validando la estructura funcional del menú.
- Se reemplazó la aserción sobre `v06.04.26` por una validación basada en patrón para la etiqueta de versión mostrada en el footer.
- Se simplificó la validación del orden visual para evitar acoplarla al formateo exacto del atributo `style`.

## Impacto esperado

- El test sigue cubriendo la reorganización del menú y el acceso al footer de versiones.
- La prueba deja de fallar por cada nueva release del changelog o por cambios menores de formateo HTML.
