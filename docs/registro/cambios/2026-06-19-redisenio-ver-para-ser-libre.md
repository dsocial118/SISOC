# 2026-06-19 - Rediseño de Ver para ser libre

## Contexto

- Se adecuaron las pantallas del módulo Ver para ser libre al sistema visual definido en Figma.
- Los recuadros negros del tablero se interpretaron como separadores del lienzo y no como componentes de interfaz.

## Cambios aplicados

- Se unificaron colores, jerarquías, encabezados turquesa, paneles, tablas, formularios, botones y comportamiento responsive del módulo.
- Se rediseñaron el buscador/listado de itinerarios, el detalle del itinerario y las confirmaciones de borrado.
- Los formularios y submódulos existentes heredan el mismo lenguaje visual sin cambiar sus contratos ni reglas de negocio.
- Se agregaron acciones de borrado lógico para itinerarios y jornadas, protegidas por los permisos Django existentes `delete_itinerariovpsl` y `delete_jornadavpsl`.
- Se extendió el lienzo azul del diseño a toda el área de contenido y se ajustaron densidad, espaciado, botones, tablas y jerarquías para acercarlos al Figma.
- Se incorporó búsqueda de itinerarios por código, provincia, estado o referente.
- Se reorganizó el detalle de jornada con mapa compacto, datos de ubicación, checklist horizontal, registros nominales y laboratorio/cierre apilados.
- Se agregó borrado lógico de registros nominales con el permiso `delete_registronominalvpsl`.

- Se alineó la paleta con los tokens exactos del diseño (`#3E5A7E`, `#232D4F`, `#3B8681` y `#E7BA61`).
- Se diferenció la jerarquía de tablas: los listados independientes conservan encabezado turquesa, mientras que las tablas contenidas en bloques usan encabezados de columna azul marino debajo del título turquesa.

## Impacto esperado

- Cambia la presentación visual del módulo y sus submódulos.
- Los filtros, altas, ediciones, validaciones RENAPER, exportaciones y transiciones de workflow conservan su funcionamiento.
- Itinerarios y jornadas pueden darse de baja desde las tablas mediante modal de confirmación; la eliminación es lógica y en cascada según el mecanismo común del proyecto.

## Validación

- Suite `ver_para_ser_libre/tests/test_workflow.py`: 65 tests OK.
- `djlint --check` sobre los templates modificados: OK.
- `black --check` sobre Python modificado: OK.
- `pylint` sobre vistas y URLs: 10/10.
- `git diff --check`: OK.

## Riesgos y rollback

- Riesgo principal: diferencias menores de proporción entre el Figma estático y datos reales con textos extensos; el diseño incluye adaptación responsive y tablas desplazables.
- Rollback: revertir este cambio restaura los templates/CSS y elimina las dos rutas de baja lógica agregadas.
