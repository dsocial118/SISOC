# Diseño: migración de sidebar a topbar pura

## Problema

La navegación principal de SISOC dependía de un sidebar fijo que ocupaba ancho constante, condicionaba el layout del contenido y agregaba complejidad de colapso/hover/responsive.

## Decisión

Se adopta una topbar pura para desktop con estas reglas:

- La navegación principal vive en el header.
- Los grupos con profundidad se muestran como paneles desplegables amplios.
- El lateral permanente desaparece en desktop.
- En mobile se conserva un panel temporal tipo offcanvas para no saturar el header.

## Alcance

- `includes/base.html` y `includes/new_base.html`
- headers y parciales de navegación asociados
- estilos y JS específicos de navegación

## Criterios UX

- Liberar el ancho lateral para contenido útil.
- Reducir la fricción visual del patrón sidebar mini/collapse.
- Mantener permisos, rutas y árbol actual del menú sin reescritura funcional.
- Evitar una topbar “plana” imposible de escanear, usando dropdowns amplios para módulos complejos.

## Riesgos aceptados

- Los menús profundos siguen heredando parte de la estructura HTML original, por lo que el refinamiento visual posterior puede requerir un segundo pase.
- En mobile no se replica la topbar pura; se usa offcanvas por practicidad y legibilidad.

## Validación prevista

- Revisión manual desktop y mobile.
- Verificación de estados activos.
- Chequeo de render de templates modificados.
