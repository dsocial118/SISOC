# Mobile Hub de espacios: filtros colapsados por defecto

## Cambio

En el Hub de espacios de la app mobile, la tarjeta de filtros superior ahora inicia colapsada.

## Alcance

- Pantalla afectada: `mobile/src/features/home/OrganizationHomePage.tsx`
- No se modifican criterios de filtrado ni navegación.

## Impacto visible

- La sección `Filtros` aparece cerrada al ingresar a la pantalla.
- El usuario puede expandirla manualmente desde el encabezado del bloque.
- Los espacios directos ahora se presentan dentro de una card propia titulada `Espacios`, consistente con el patrón visual del listado.
- Los acordeones de la pantalla usan chevrons verticales (`abajo/arriba`) para reforzar que despliegan contenido en la misma vista.
- Los chevrons de navegación dentro de las cards de espacios quedan fijados en el lateral derecho y centrados respecto de toda la card para hacer más clara la acción de ingreso.
